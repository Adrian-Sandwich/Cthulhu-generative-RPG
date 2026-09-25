"""Real PostgreSQL integration; no mock substitute for coordination guarantees.

CTHULHU_TEST_DATABASE_URL must point at a disposable test database. Every test
owns a uniquely named schema, and only that schema is removed during cleanup.
"""

import os
import threading
from uuid import uuid4
from unittest.mock import patch

import pytest
from psycopg import sql

from core.postgres_store import PostgresStore, StorageUnavailable

DSN = os.environ.get('CTHULHU_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not DSN, reason='Set CTHULHU_TEST_DATABASE_URL for PostgreSQL integration')


@pytest.fixture
def store():
    schema = 'cthulhu_test_' + uuid4().hex
    store = PostgresStore(DSN, schema)
    store.initialize()
    try:
        yield store
    finally:
        store.close()
        assert schema.startswith('cthulhu_test_') and len(schema) == 45
        with store.connect() as connection:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


@pytest.fixture
def apps(store, tmp_path):
    from app import create_app
    def fake_chat(self, *args, **kwargs):
        text = 'The shadows shift.'
        if kwargs.get('on_chunk'):
            kwargs['on_chunk'](text)
        return text
    with patch('core.llm_client.LLMClient.chat', fake_chat), patch(
        'core.llm_client.LLMClient.chat_with_tools',
        return_value={'narrative': '', 'tool_calls': [], 'fallback': True},
    ):
        config = {'DATABASE_URL': DSN, 'DATABASE_SCHEMA': store.schema,
                  'SECRET_KEY': 'shared-test-only-key', 'ADMIN_TOKEN': 'test-admin'}
        instances = [create_app(dict(config, DATA_DIR=str(tmp_path / str(i)))) for i in range(2)]
        try:
            yield instances
        finally:
            for app in instances:
                app.extensions['cthulhu'].store.close()


def test_short_pool_reuses_connections_but_session_lock_stays_dedicated(store):
    pooled = PostgresStore(DSN, store.schema, pool_size=1, pool_timeout=1)
    try:
        with pooled.short_connection() as first:
            pid = first.info.backend_pid
            with pytest.raises(StorageUnavailable):
                with pooled.short_connection():
                    pytest.fail('pool exceeded its size')
            with pooled.locked('separate') as owner:
                assert owner.connection.info.backend_pid != pid
        with pooled.short_connection() as second:
            assert second.info.backend_pid == pid
        with pooled.locked('separate', blocking=False) as owner:
            assert owner is not None
    finally:
        pooled.close()


def test_short_pool_recovers_dead_connection(store):
    pooled = PostgresStore(DSN, store.schema, pool_size=1, pool_timeout=2)
    try:
        with pooled.short_connection() as connection:
            pid = connection.info.backend_pid
        with store.connect() as killer:
            killer.execute('SELECT pg_terminate_backend(%s)', (pid,))
        with pooled.short_connection() as replacement:
            assert replacement.info.backend_pid != pid
            assert replacement.execute('SELECT 1').fetchone() == (1,)
    finally:
        pooled.close()


def test_real_json_save_migrates_with_inventory_discoveries_and_receipts(store, tmp_path):
    from app import create_app
    from tools.migrate_postgres import import_saves
    config = {'DATABASE_URL': '', 'DATA_DIR': str(tmp_path / 'json'),
              'SECRET_KEY': 'migration-test-key'}
    source = create_app(config).test_client()
    start = source.post('/api/game/start', json={'name': 'Migration', 'archetype': 'scholar'}).json
    command = {'action': 'take flashlight', 'action_id': uuid4().hex, 'game_id': start['game_id']}
    receipt = source.post('/api/game/action', json=command).json
    source.post('/api/game/action', json={'action': 'search for the keeper key'})
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
        source.post('/api/game/roll')
    before = source.get('/api/game/state').json
    assert import_saves(store, config['DATA_DIR'])['would_import'] == 1
    assert import_saves(store, config['DATA_DIR'], apply=True)['imported'] == 1
    assert import_saves(store, config['DATA_DIR'], apply=True)['unchanged'] == 1
    destination = create_app(dict(config, DATABASE_URL=DSN, DATABASE_SCHEMA=store.schema,
                                  DATA_DIR=str(tmp_path / 'postgres')))
    try:
        client = destination.test_client()
        client.set_cookie('session', source.get_cookie('session').value)
        assert client.get('/api/game/state').json == before
        assert client.post('/api/game/action', json=command).json == receipt
        assert client.get('/api/game/state').json['investigator']['inventory'] == ['Flashlight']
        assert len(client.get('/api/game/state').json['discoveries']) == 1
    finally:
        destination.extensions['cthulhu'].store.close()
        for gs in source.application.extensions['cthulhu'].sessions.values():
            gs.engine.close()


def test_ending_objectives_follow_player_between_servers(apps):
    a, b, sid, command = clients(apps)
    command['action'] = 'I navigate the coast'
    assert a.post('/api/game/action', json=command).json['pending_roll']['skill'] == 'navigate'
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
        assert b.post('/api/game/roll').json['roll_success']
    finish = dict(command, action='leave the island', action_id=uuid4().hex)
    with patch('core.llm_client.LLMClient.chat', side_effect=AssertionError('model decided ending')):
        result = a.post('/api/game/action', json=finish)
        assert result.status_code == 200 and result.json['ending']['type'] == 'escape'
        assert b.post('/api/game/action', json=finish).json == result.json


def test_two_servers_racing_new_ids_cannot_claim_reward_twice(apps, store):
    from concurrent.futures import ThreadPoolExecutor
    a, b, sid, command = clients(apps)
    first = dict(command, action='take flashlight')
    second = dict(first, action_id=uuid4().hex)
    barrier = threading.Barrier(2)
    def claim(client, body):
        barrier.wait(timeout=5)
        return client.post('/api/game/action', json=body)
    with ThreadPoolExecutor(2) as pool:
        futures = [pool.submit(claim, a, first), pool.submit(claim, b, second)]
        results = [future.result(timeout=10) for future in futures]
    assert sorted(r.status_code for r in results) == [200, 400]
    state = store.read(sid)['game_state']
    assert state['claimed_rewards'] == ['flashlight']
    assert state['investigator']['inventory'] == ['Flashlight']
    assert state['turn'] == 2
    winner = 0 if results[0].status_code == 200 else 1
    body = [first, second][winner]
    assert b.post('/api/game/action', json=body).json == results[winner].json


def clients(apps):
    a, b = [app.test_client() for app in apps]
    start = a.post('/api/game/start', json={'name': 'Tester', 'archetype': 'scholar'})
    assert start.status_code == 200, start.get_data(as_text=True)
    # Transfer the real signed browser cookie across independent app instances.
    b.set_cookie('session', a.get_cookie('session').value)
    with a.session_transaction() as session:
        sid = session['sid']
    command = {'action': 'look around', 'action_id': uuid4().hex,
               'game_id': start.get_json()['game_id']}
    return a, b, sid, command


@pytest.mark.parametrize('stream', [False, True])
def test_two_servers_share_state_receipts_and_reset(apps, store, stream):
    import json
    a, b, sid, command = clients(apps)
    before = b.get('/api/game/state').get_json()['turn']
    result = a.post('/api/game/action/stream' if stream else '/api/game/action', json=command)
    assert result.status_code == 200
    payload = (json.loads(result.get_data(as_text=True).split('event: done\ndata: ')[1].split('\n\n')[0])
               if stream else result.get_json())
    assert b.get('/api/game/state').get_json()['turn'] > before
    with patch('core.game_generative.GenerativeGameEngine.process_player_action',
               side_effect=AssertionError('duplicate')):
        assert b.post('/api/game/action', json=command).get_json() == payload
    assert b.get('/api/game/actions/' + command['action_id']).get_json()['status'] == 'completed'
    assert not (apps[0].extensions['cthulhu'].data_dir / 'saves').exists()
    assert b.post('/api/game/reset').status_code == 200
    assert not store.exists(sid)
    assert a.get('/api/game/state').status_code == 400


def test_concurrent_servers_execute_once_and_can_read_progress(apps, store):
    from core.game_generative import GenerativeGameEngine
    a, b, sid, command = clients(apps)
    entered, release = threading.Event(), threading.Event()
    calls, results = [], []
    original = GenerativeGameEngine.process_player_action
    def slow(self, *args, **kwargs):
        calls.append(1)
        entered.set()
        assert release.wait(10)
        return original(self, *args, **kwargs)
    def request(client):
        results.append(client.post('/api/game/action', json=command).get_json())
    with patch.object(GenerativeGameEngine, 'process_player_action', slow):
        first, second = threading.Thread(target=request, args=(a,)), threading.Thread(target=request, args=(b,))
        first.start()
        try:
            assert entered.wait(4)
            # Another server must not mistake the running receipt for an orphan.
            status = b.get('/api/game/actions/' + command['action_id']).get_json()
            assert status['status'] == 'running'
            second.start()
            assert calls == [1]
        finally:
            release.set()
            first.join(5)
            if second.ident:
                second.join(5)
    assert len(results) == 2 and results[0] == results[1]
    assert calls == [1]


def test_lost_lock_connection_cannot_overwrite_new_owner(store):
    sid = uuid4().hex
    with store.locked(sid) as stale:
        stale.write(sid, {'version': 1})
        backend = stale.connection.info.backend_pid
        with store.connect() as admin:
            admin.execute('SELECT pg_terminate_backend(%s)', (backend,))
        with store.locked(sid) as current:
            current.write(sid, {'version': 2})
            with pytest.raises(StorageUnavailable):
                stale.write(sid, {'version': 3})
    assert store.read(sid) == {'version': 2}


def test_shared_rate_limit_and_feedback(apps):
    a, b, _, _ = clients(apps)
    assert a.post('/api/feedback', json={'text': 'A good fright', 'rating': 5}).status_code == 200
    stats = b.get('/api/admin/stats?token=test-admin').get_json()
    assert stats['total_saves'] == 1
    assert stats['feedback_count'] == 1
    # One start already consumed from this shared IP budget.
    responses = [(a if i % 2 else b).post('/api/game/start', json=[]).status_code for i in range(6)]
    assert responses == [400] * 5 + [429]


def test_orphaned_running_receipt_restores_checkpoint(apps, store):
    a, b, sid, command = clients(apps)
    with store.locked(sid) as owner:
        payload = owner.read(sid)
        payload['app_state']['actions'][command['action_id']] = {
            'status': 'running', 'action': command['action'],
        }
        owner.write(sid, payload)
    with patch('core.game_generative.GenerativeGameEngine.process_player_action',
               side_effect=AssertionError('reexecuted orphan')):
        receipt = b.get('/api/game/actions/' + command['action_id']).get_json()
        assert receipt['status'] == 'failed'
        assert a.post('/api/game/action', json=command).status_code == 409
    assert store.read(sid)['game_state']['turn'] == 1


def test_import_is_dry_by_default_and_never_overwrites(store, tmp_path):
    import json
    from dataclasses import asdict
    from core.archetypes import create_investigator
    from core.state import GameState
    from tools.migrate_postgres import import_saves
    sid = uuid4().hex
    directory = tmp_path / 'saves' / 'generative'
    directory.mkdir(parents=True)
    path = directory / (sid + '.json')
    state = GameState(turn=1, location='room', narrative=[],
                      investigator=create_investigator('Imported', 'scholar'),
                      recent_actions=[], game_phase='exploring', victory_condition=None,
                      ending_reached=None, ending_narrative=None)
    payload = {'metadata': {'session_id': sid, 'model': 'mock'}, 'game_state': asdict(state)}
    path.write_text(json.dumps(payload), encoding='utf-8')
    original = path.read_bytes()
    assert import_saves(store, tmp_path)['would_import'] == 1
    assert not store.exists(sid)
    assert import_saves(store, tmp_path, apply=True)['imported'] == 1
    assert import_saves(store, tmp_path, apply=True)['unchanged'] == 1
    assert path.read_bytes() == original
    payload['game_state']['turn'] = 2
    path.write_text(json.dumps(payload), encoding='utf-8')
    assert import_saves(store, tmp_path, apply=True)['conflicts'] == 1
    assert store.read(sid)['game_state']['turn'] == 1
    assert original != path.read_bytes()  # only this test changed the source


def test_postgres_requires_shared_cookie_key(store, monkeypatch):
    from app import create_app
    monkeypatch.delenv('SECRET_KEY', raising=False)
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app({'DATABASE_URL': DSN, 'DATABASE_SCHEMA': store.schema})


def _process_turn(dsn, schema, sid, command, data_dir, entered, release, results):
    """Spawn-safe worker: an independent interpreter, app and DB connection."""
    from app import create_app
    from core.game_generative import GenerativeGameEngine
    original = GenerativeGameEngine.process_player_action
    def action(self, *args, **kwargs):
        results.put(('executed', os.getpid()))
        entered.set()
        if not release.wait(15):
            raise RuntimeError('test release timed out')
        return original(self, *args, **kwargs)
    app = create_app({'DATABASE_URL': dsn, 'DATABASE_SCHEMA': schema,
                      'SECRET_KEY': 'shared-test-only-key', 'DATA_DIR': data_dir})
    client = app.test_client()
    with client.session_transaction() as session:
        session['sid'] = sid
    with patch.object(GenerativeGameEngine, 'process_player_action', action), patch(
        'core.llm_client.LLMClient.chat', return_value='The wind rises.',
    ), patch('core.llm_client.LLMClient.chat_with_tools',
             return_value={'narrative': '', 'tool_calls': [], 'fallback': True}):
        response = client.post('/api/game/action', json=command)
        results.put(('response', (response.status_code, response.get_json())))


def test_separate_processes_execute_duplicate_exactly_once(apps, store, tmp_path):
    import multiprocessing
    import time
    from core.postgres_store import lock_key
    a, b, sid, command = clients(apps)
    context = multiprocessing.get_context('spawn')
    entered, release, results = context.Event(), context.Event(), context.Queue()
    workers = [context.Process(target=_process_turn, args=(
        DSN, store.schema, sid, command, str(tmp_path / str(i)), entered, release, results,
    )) for i in range(2)]
    messages = []
    try:
        workers[0].start()
        assert entered.wait(10)
        workers[1].start()
        # Verify that the second OS process actually waits on PostgreSQL,
        # rather than merely replaying after the first has already finished.
        key = lock_key(store.schema + ':game:' + sid) & ((1 << 64) - 1)
        deadline = time.monotonic() + 8
        waiting = False
        with store.connect() as connection:
            while time.monotonic() < deadline:
                waiting = connection.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_locks WHERE locktype='advisory' "
                    "AND classid=%s AND objid=%s AND objsubid=1 AND NOT granted)",
                    (key >> 32, key & 0xffffffff),
                ).fetchone()[0]
                if waiting:
                    break
                time.sleep(0.05)
        assert waiting, 'second process never contended for the session lock'
        assert b.get('/api/game/actions/' + command['action_id']).get_json()['status'] == 'running'
        release.set()
        messages = [results.get(timeout=15) for _ in range(3)]
        for worker in workers:
            worker.join(10)
            assert worker.exitcode == 0
    finally:
        release.set()
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(5)
        results.close()
    assert sum(kind == 'executed' for kind, _ in messages) == 1
    responses = [payload for kind, payload in messages if kind == 'response']
    assert len(responses) == 2 and responses[0] == responses[1]
    assert responses[0][0] == 200


def test_ambiguous_commit_is_recovered_without_reexecution(apps, store, monkeypatch):
    from core.postgres_store import LockedSessionStore
    a, b, sid, command = clients(apps)
    original = LockedSessionStore.write
    def lost_acknowledgment(self, identity, payload):
        result = original(self, identity, payload)
        receipt = (payload.get('app_state') or {}).get('actions', {}).get(command['action_id'], {})
        if receipt.get('status') == 'completed':
            self.connection.close()
            raise StorageUnavailable('simulated lost commit acknowledgment')
        return result
    with monkeypatch.context() as scoped:
        scoped.setattr(LockedSessionStore, 'write', lost_acknowledgment)
        assert a.post('/api/game/action', json=command).status_code == 503
    with patch('core.game_generative.GenerativeGameEngine.process_player_action',
               side_effect=AssertionError('ambiguous commit executed twice')):
        result = b.post('/api/game/action', json=command)
    assert result.status_code == 200
    assert store.read(sid)['app_state']['actions'][command['action_id']]['status'] == 'completed'


def test_crashed_process_releases_lock_and_leaves_recoverable_checkpoint(apps, store, tmp_path):
    import multiprocessing
    a, b, sid, command = clients(apps)
    context = multiprocessing.get_context('spawn')
    entered, release, results = context.Event(), context.Event(), context.Queue()
    worker = context.Process(target=_process_turn, args=(
        DSN, store.schema, sid, command, str(tmp_path), entered, release, results,
    ))
    worker.start()
    try:
        assert entered.wait(10)
        worker.terminate()
        worker.join(5)
        assert not worker.is_alive()
        receipt = b.get('/api/game/actions/' + command['action_id']).get_json()
        assert receipt['status'] == 'failed'
        assert store.read(sid)['game_state']['turn'] == 1
        assert a.post('/api/game/action', json=command).status_code == 409
    finally:
        if worker.is_alive():
            worker.terminate()
            worker.join(5)
        results.close()


def test_legacy_save_gets_one_shared_game_identity(apps, store):
    a, b, sid, command = clients(apps)
    with store.locked(sid) as owner:
        payload = owner.read(sid)
        payload['app_state'] = None
        owner.write(sid, payload)
    identity = a.get('/api/game/state').get_json()['game_id']
    assert b.get('/api/game/state').get_json()['game_id'] == identity
    command['game_id'] = identity
    assert b.post('/api/game/action', json=command).status_code == 200


def test_unavailable_database_fails_closed_without_json_fallback(apps, tmp_path):
    from app import create_app
    app = create_app({'DATABASE_URL': DSN, 'DATABASE_SCHEMA': 'missing_' + uuid4().hex,
                      'SECRET_KEY': 'test-only', 'DATA_DIR': str(tmp_path)})
    client = app.test_client()
    health = client.get('/api/health')
    assert health.status_code == 503
    assert health.get_json()['storage'] == 'postgres'
    response = client.post('/api/game/start', json={'name': 'Should not save'})
    assert response.status_code == 503
    assert not (tmp_path / 'saves').exists()
