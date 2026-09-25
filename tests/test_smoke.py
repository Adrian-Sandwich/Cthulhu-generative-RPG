#!/usr/bin/env python3
"""
Fast smoke/regression suite — no Ollama, no network. Mocks the LLM and drives
a fresh Flask app instance per test to catch regressions in the hot path and
the safety guards. Run: pytest tests/test_smoke.py -q
"""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- fixtures --------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_llm_degradation():
    """The degraded-turn counter is process-wide by design (it answers "is the
    model answering at all", not a per-session question), which makes tests
    order-dependent unless it is reset."""
    from core.llm_client import LLMClient
    LLMClient.degraded_turns = 0
    LLMClient.last_error = None
    yield
    LLMClient.degraded_turns = 0
    LLMClient.last_error = None


def _make_app(data_dir):
    """Build a fresh app instance isolated to the given data directory."""
    import app as app_module
    return app_module.create_app({"DATA_DIR": str(data_dir)})


# A valid narrator response. World tags are tested separately as adversarial inputs.
CANNED_DM = (
    "You press deeper into the dark. Something stirs. "
    "[NPC_DIALOGUE: warner]"
)


@pytest.fixture
def client(tmp_path):
    """A fresh app client with storage redirected to a temp dir and the LLM
    mocked to a canned, genuinely tag-rich response (see CANNED_DM)."""

    def fake_chat(self, *a, **k):
        on = k.get("on_chunk")
        txt = CANNED_DM
        if on:
            on(txt)
        return txt

    def fake_tools(self, *a, **k):
        return {"narrative": "", "tool_calls": [], "fallback": True}

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools", fake_tools):
        yield _make_app(tmp_path).test_client()


def _start(client, **kw):
    body = {"name": "Tester", "archetype": "scholar"}
    body.update(kw)
    return client.post("/api/game/start", json=body)


# --- core flow -------------------------------------------------------------

def test_start_and_state(client):
    r = _start(client)
    assert r.status_code == 200 and r.get_json()["success"]
    s = client.get("/api/game/state").get_json()
    assert s["turn"] == 1
    assert s["location"]


def test_action_turn(client):
    _start(client)
    r = client.post("/api/game/action", json={"action": "look around the room"})
    assert r.status_code == 200
    assert r.get_json()["success"]


def test_engine_movement_has_no_unsolicited_reward_over_http(client):
    _start(client)
    r = client.post("/api/game/action", json={"action": "go to interior"})
    assert r.status_code == 200, r.get_data(as_text=True)
    after = client.get("/api/game/state").get_json()
    assert after["location"] == "Lighthouse Interior"
    assert after["investigator"]["inventory"] == []


def test_action_stream(client):
    _start(client)
    r = client.post("/api/game/action/stream", json={"action": "look around the room"})
    assert r.status_code == 200
    assert r.mimetype == "text/event-stream"
    data = r.get_data(as_text=True)
    assert "data:" in data
    assert "event: done" in data


def test_action_stream_survives_a_slow_first_chunk(tmp_path):
    """The SSE generator must survive the queue-timeout branch.

    Regression: that branch read `request.is_disconnected` — an attribute Flask
    does not have, on a proxy that is unbound once the request context tears
    down — so it raised RuntimeError and the stream 500'd, silently degrading
    every turn to the non-streaming fallback. The default fixture's LLM answers
    instantly, so `q.get(timeout=1.0)` never times out and the branch was
    unreachable. This one makes the model slow enough to reach it.
    """
    import time

    def slow_chat(self, *a, **k):
        on = k.get("on_chunk")
        time.sleep(1.6)          # longer than the generator's 1.0s queue timeout
        if on:
            on(CANNED_DM)
        return CANNED_DM

    with patch("core.llm_client.LLMClient.chat", slow_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        c = _make_app(tmp_path).test_client()
        c.post("/api/game/start", json={"name": "Slow", "archetype": "scholar"})
        r = c.post("/api/game/action/stream", json={"action": "listen at the door"})
        assert r.status_code == 200
        data = r.get_data(as_text=True)

    assert "event: done" in data, data[-400:]
    assert "Working outside of request context" not in data
    assert "event: error" not in data, data[-400:]


def test_roll_flow(client):
    _start(client)
    r = client.post("/api/game/action", json={"action": "climb the slick cliff"}).get_json()
    if r.get("pending_roll"):
        rr = client.post("/api/game/roll").get_json()
        assert rr["success"] and "roll" in rr


def test_reset(client):
    _start(client)
    assert client.post("/api/game/reset").get_json()["success"]


# --- input guards ----------------------------------------------------------

def _command(client, action_id='recovery-test-001', action='look around'):
    state = client.get('/api/game/state').get_json()
    return {'action': action, 'action_id': action_id, 'game_id': state['game_id']}


def _restart_client(client):
    game = client.application.extensions['cthulhu']
    fresh = _make_app(game.data_dir).test_client()
    with client.session_transaction() as old:
        sid = old['sid']
    with fresh.session_transaction() as new:
        new['sid'] = sid
    return fresh


@pytest.mark.parametrize('first_stream', [False, True])
def test_action_receipt_replays_across_endpoints_and_restart(client, first_stream):
    import json
    _start(client)
    command = _command(client)
    endpoint = '/api/game/action/stream' if first_stream else '/api/game/action'
    first = client.post(endpoint, json=command)
    if first_stream:
        body = first.get_data(as_text=True)
        payload = json.loads(body.split('event: done\ndata: ')[1].split('\n\n')[0])
    else:
        payload = first.get_json()
    state = client.get('/api/game/state').get_json()
    fresh = _restart_client(client)
    with patch('core.game_generative.GenerativeGameEngine.process_player_action',
               side_effect=AssertionError('duplicate execution')):
        assert fresh.post('/api/game/action', json=command).get_json() == payload
        stream = fresh.post('/api/game/action/stream', json=command).get_data(as_text=True)
        assert 'event: done' in stream
        receipt = fresh.get('/api/game/actions/' + command['action_id']).get_json()
    assert receipt['status'] == 'completed'
    assert receipt['result'] == payload
    assert fresh.get('/api/game/state').get_json() == state


def test_duplicate_id_conflicts_and_new_game_rejects_old_command(client):
    _start(client)
    command = _command(client)
    assert client.post('/api/game/action', json=command).status_code == 200
    assert client.post('/api/game/action', json=dict(command, action='run away')).status_code == 409
    _start(client)
    assert client.post('/api/game/action', json=command).status_code == 409
    assert client.get('/api/game/actions/' + command['action_id'],
                      query_string={'game_id': command['game_id']}).status_code == 409


@pytest.mark.parametrize('status', ['pending', 'running'])
def test_restart_marks_uncommitted_turn_failed_without_reexecuting(client, status):
    _start(client)
    command = _command(client)
    game = client.application.extensions['cthulhu']
    gs = next(iter(game.sessions.values()))
    before = gs.engine.state.turn
    gs.actions[command['action_id']] = {'action': command['action'], 'status': status}
    game.autosave(gs, strict=True)
    gs.engine.state.turn += 10  # lost in-memory work at the simulated crash
    fresh = _restart_client(client)
    with patch('core.game_generative.GenerativeGameEngine.process_player_action',
               side_effect=AssertionError('interrupted turn was reexecuted')):
        receipt = fresh.get('/api/game/actions/' + command['action_id']).get_json()
        assert receipt['status'] == 'failed'
        assert fresh.post('/api/game/action', json=command).status_code == 409
    assert fresh.get('/api/game/state').get_json()['turn'] == before


def test_concurrent_duplicate_runs_once_and_status_does_not_block(client, monkeypatch):
    import threading
    _start(client)
    command = _command(client)
    game = client.application.extensions['cthulhu']
    gs = next(iter(game.sessions.values()))
    original = gs.engine.process_player_action
    entered, release = threading.Event(), threading.Event()
    calls, responses = [], []
    def slow(*args, **kwargs):
        calls.append(1)
        entered.set()
        assert release.wait(10)
        return original(*args, **kwargs)
    monkeypatch.setattr(gs.engine, 'process_player_action', slow)
    def duplicate_client():
        other = client.application.test_client()
        with other.session_transaction() as session:
            session['sid'] = gs.sid
        return other
    def send():
        responses.append(duplicate_client().post('/api/game/action', json=command).get_json())
    first = threading.Thread(target=send)
    second = threading.Thread(target=send)
    first.start()
    try:
        assert entered.wait(3)
        second.start()
        receipt = duplicate_client().get('/api/game/actions/' + command['action_id']).get_json()
        assert receipt['status'] == 'running'
        assert calls == [1]
    finally:
        release.set()
        first.join(5)
        if second.ident:
            second.join(5)
    assert len(responses) == 2 and responses[0] == responses[1]
    assert calls == [1]


def test_failed_commit_rolls_back_mechanics_and_never_reports_success(client, monkeypatch):
    _start(client)
    command = _command(client)
    game = client.application.extensions['cthulhu']
    gs = next(iter(game.sessions.values()))
    before = client.get('/api/game/state').get_json()
    original = gs.engine.save_game
    def fail_commit(app_state=None):
        receipt = app_state.get('actions', {}).get(command['action_id'], {})
        if receipt.get('status') == 'completed':
            raise OSError('disk full')
        return original(app_state=app_state)
    monkeypatch.setattr(gs.engine, 'save_game', fail_commit)
    response = client.post('/api/game/action', json=command)
    assert response.status_code == 503
    assert client.get('/api/game/state').get_json() == before
    receipt = client.get('/api/game/actions/' + command['action_id']).get_json()
    assert receipt['status'] == 'failed'
    with patch.object(gs.engine, 'process_player_action', side_effect=AssertionError('reexecuted')):
        assert client.post('/api/game/action', json=command).status_code == 503


def test_receipts_are_private_to_the_session(client):
    _start(client)
    command = _command(client)
    client.post('/api/game/action', json=command)
    other = client.application.test_client()
    _start(other)
    assert other.get('/api/game/actions/' + command['action_id']).status_code == 404


@pytest.mark.parametrize('fail_on', [1, 2])
def test_checkpoint_failure_never_calls_model(client, monkeypatch, fail_on):
    _start(client)
    command = _command(client)
    game = client.application.extensions['cthulhu']
    gs = next(iter(game.sessions.values()))
    original = gs.engine.save_game
    count = 0
    def fail_checkpoint(app_state=None):
        nonlocal count
        count += 1
        if count == fail_on:
            raise OSError('checkpoint failed')
        return original(app_state=app_state)
    monkeypatch.setattr(gs.engine, 'save_game', fail_checkpoint)
    with patch.object(gs.engine, 'process_player_action', side_effect=AssertionError('model called')):
        assert client.post('/api/game/action', json=command).status_code == 503
    assert client.get('/api/game/state').get_json()['turn'] == 1
    receipt = client.get('/api/game/actions/' + command['action_id'])
    if fail_on == 1:
        assert receipt.status_code == 404
    else:
        assert receipt.get_json()['status'] == 'failed'


def test_failed_action_restores_state_and_replays_error(client, monkeypatch):
    _start(client)
    command = _command(client)
    game = client.application.extensions['cthulhu']
    gs = next(iter(game.sessions.values()))
    before = client.get('/api/game/state').get_json()
    def partial(*args, **kwargs):
        gs.engine.state.turn += 1
        gs.investigator.characteristics['HP'] = 0
        raise RuntimeError('partial failure')
    monkeypatch.setattr(gs.engine, 'process_player_action', partial)
    first = client.post('/api/game/action', json=command)
    assert first.status_code == 500
    assert client.get('/api/game/state').get_json() == before
    fresh = _restart_client(client)
    assert fresh.post('/api/game/action', json=command).get_json() == first.get_json()


def test_client_action_id_requires_game_identity(client):
    _start(client)
    assert client.post('/api/game/action', json={
        'action': 'look', 'action_id': 'valid-id-001',
    }).status_code == 400


@pytest.mark.parametrize('action_id', ['', 'short', '../escape', [], 42, 'x' * 129])
def test_invalid_action_ids_do_not_execute(client, action_id):
    _start(client)
    assert client.post('/api/game/action', json={'action': 'look', 'action_id': action_id}).status_code == 400


def test_completed_receipt_replays_even_with_a_pending_roll(client):
    _start(client)
    command = _command(client)
    first = client.post('/api/game/action', json=command).get_json()
    gs = next(iter(client.application.extensions['cthulhu'].sessions.values()))
    gs.pending_roll = {'skill': 'spot_hidden', 'difficulty': 'regular'}
    assert client.post('/api/game/action', json=command).get_json() == first

@pytest.mark.parametrize('endpoint', ['/api/game/start', '/api/game/action',
                                      '/api/game/action/stream', '/api/feedback'])
@pytest.mark.parametrize('body', [[], ['bad'], 'bad', 42, False, None])
def test_json_must_be_an_object(client, endpoint, body):
    import json
    _start(client)
    before = client.get('/api/game/state').get_json()
    response = client.post(endpoint, data=json.dumps(body), content_type='application/json')
    assert response.status_code == 400
    assert response.is_json
    assert client.get('/api/game/state').get_json() == before


@pytest.mark.parametrize('fields', [{'name': []}, {'name': ' '}, {'name': 'a' * 101},
                                   {'archetype': []}, {'archetype': 'unknown'}])
def test_invalid_character_does_not_replace_game(client, fields):
    _start(client)
    before = client.get('/api/game/state').get_json()
    assert _start(client, **fields).status_code == 400
    assert client.get('/api/game/state').get_json() == before


def test_forged_ip_headers_do_not_reset_rate_limit(client):
    codes = [client.post('/api/game/start', json=[], headers={
        'CF-Connecting-IP': f'192.0.2.{i}', 'X-Forwarded-For': f'198.51.100.{i}'
    }).status_code for i in range(8)]
    assert codes == [400] * 6 + [429] * 2


@pytest.mark.parametrize('peer,forwarded,expected', [
    ('127.0.0.1', '192.0.2.1', '192.0.2.1'),
    ('127.0.0.1', '203.0.113.9, 192.0.2.1', '192.0.2.1'),
    ('127.0.0.1', '192.0.2.1, 10.0.0.2', '192.0.2.1'),
    ('192.0.2.2', '203.0.113.9', '192.0.2.2'),
    ('127.0.0.1', 'garbage', '127.0.0.1'),
    ('::1', '2001:db8::1', '2001:db8::1'),
])
def test_trusted_proxy_chain(client, peer, forwarded, expected):
    from ipaddress import ip_network
    game = client.application.extensions['cthulhu']
    game.trusted_proxies = [ip_network(cidr) for cidr in ['127.0.0.1/32', '10.0.0.2/32', '::1/128']]
    with client.application.test_request_context('/', environ_base={'REMOTE_ADDR': peer},
                                                 headers={'X-Forwarded-For': forwarded}):
        assert game.client_ip() == expected


@pytest.mark.parametrize('stage', ['process_player_action', 'apply_turn_consequences'])
def test_stream_reports_worker_exception(client, monkeypatch, stage):
    _start(client)
    game = client.application.extensions['cthulhu']
    gs = next(iter(game.sessions.values()))
    def fail(*args, **kwargs):
        raise RuntimeError('simulated failure')
    monkeypatch.setattr(gs.engine, stage, fail)
    response = client.post('/api/game/action/stream', json={'action': 'look'})
    body = response.get_data(as_text=True)
    assert 'event: error' in body and 'simulated failure' in body
    assert 'event: done' not in body
    assert gs.lock.acquire(blocking=False)
    gs.lock.release()


def test_slow_stream_consumer_still_receives_saved_result(client, monkeypatch):
    import threading
    _start(client)
    gs = next(iter(client.application.extensions['cthulhu'].sessions.values()))
    original = gs.engine.process_player_action
    overflowed = threading.Event()
    def burst(action, on_chunk):
        for _ in range(100):
            on_chunk('A wave breaks. ')
        overflowed.set()
        return original(action, on_chunk=on_chunk)
    monkeypatch.setattr(gs.engine, 'process_player_action', burst)
    response = client.post('/api/game/action/stream', json={'action': 'look'}, buffered=False)
    try:
        assert overflowed.wait(5), 'producer stalled on full queue'
        body = response.get_data(as_text=True)
        assert body.count('event: done') == 1
        assert 'event: error' not in body
    finally:
        response.close()


def test_disconnect_keeps_lock_until_turn_is_saved(client, monkeypatch):
    import threading
    import time
    from core.generative_save import GenerativeSave
    _start(client)
    game = client.application.extensions['cthulhu']
    gs = next(iter(game.sessions.values()))
    original = gs.engine.process_player_action
    release = threading.Event()
    closing = threading.Event()
    closed = threading.Event()
    before = gs.engine.state.turn
    command = _command(client)
    def slow(action, on_chunk):
        on_chunk('Waiting in the dark.')
        assert release.wait(15), 'test failed to release worker'
        return original(action, on_chunk=on_chunk)
    monkeypatch.setattr(gs.engine, 'process_player_action', slow)
    response = client.post('/api/game/action/stream', json=command, buffered=False)
    assert b'Waiting' in next(iter(response.response))
    def close():
        closing.set()
        try:
            response.close()
        finally:
            closed.set()
    closer = threading.Thread(target=close)
    closer.start()
    try:
        assert closing.wait(1)
        assert not closed.wait(5.2), 'disconnect released a still-active worker'
        assert gs.lock.locked()
        gs.last_access = time.time() - game.session_ttl - 1
        game._sweep_idle()
        assert game.sessions[gs.sid] is gs, 'active game was evicted'
    finally:
        release.set()
        closer.join(5)
    assert closed.is_set()
    assert not gs.lock.locked()
    assert gs.engine.state.turn > before
    metadata, _, _, _ = GenerativeSave.load(gs.sid, game.data_dir)
    assert metadata['turn'] == gs.engine.state.turn
    fresh = _restart_client(client)
    recovered = fresh.get('/api/game/actions/' + command['action_id']).get_json()
    assert recovered['status'] == 'completed'
    with patch('core.game_generative.GenerativeGameEngine.process_player_action',
               side_effect=AssertionError('disconnected turn executed twice')):
        assert fresh.post('/api/game/action', json=command).get_json() == recovered['result']


@pytest.mark.parametrize('failure', ['dump', 'replace'])
def test_failed_save_preserves_previous_autosave(client, monkeypatch, failure):
    from core.generative_save import GenerativeSave
    _start(client)
    game = client.application.extensions['cthulhu']
    gs = next(iter(game.sessions.values()))
    path = GenerativeSave._save_path(gs.sid, game.data_dir)
    previous = path.read_bytes()
    def interrupted_dump(data, output, **kwargs):
        output.write('{')
        raise OSError('interrupted write')
    def interrupted_replace(*args):
        raise OSError('replace failed')
    with monkeypatch.context() as m:
        if failure == 'dump':
            m.setattr('core.generative_save.json.dump', interrupted_dump)
        else:
            m.setattr('core.generative_save.os.replace', interrupted_replace)
        with pytest.raises(OSError):
            gs.engine.save_game()
    assert path.read_bytes() == previous
    assert not list(path.parent.glob('*.tmp'))
    assert GenerativeSave.load(gs.sid, game.data_dir)[0]['turn'] == gs.engine.state.turn
    gs.engine.state.turn += 1
    gs.engine.save_game()
    assert GenerativeSave.load(gs.sid, game.data_dir)[0]['turn'] == gs.engine.state.turn

def test_empty_action_400(client):
    _start(client)
    assert client.post("/api/game/action", json={"action": "   "}).status_code == 400


def test_oversized_action_413(client):
    _start(client)
    assert client.post("/api/game/action", json={"action": "a" * 5000}).status_code == 413


def test_bad_json_no_500(client):
    _start(client)
    r = client.post("/api/game/action", data="not json", content_type="text/plain")
    assert r.status_code < 500


def test_moderation_blocks_input(client):
    _start(client)
    assert client.post("/api/game/action", json={"action": "child porn"}).status_code == 422


def test_moderation_allows_horror(client):
    _start(client)
    r = client.post("/api/game/action", json={"action": "I stab the creature, blood everywhere"})
    assert r.status_code == 200


# --- session isolation -----------------------------------------------------

def test_two_clients_isolated(tmp_path):
    def fake_chat(self, *a, **k):
        if k.get("on_chunk"):
            k["on_chunk"]("ok")
        return "ok"

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        c1 = _make_app(tmp_path).test_client()
        c2 = _make_app(tmp_path).test_client()
        c1.post("/api/game/start", json={"name": "Alice", "archetype": "scholar"})
        c2.post("/api/game/start", json={"name": "Bob", "archetype": "detective"})
        n1 = c1.get("/api/game/state").get_json()["investigator"]["name"]
        n2 = c2.get("/api/game/state").get_json()["investigator"]["name"]
        assert n1 == "Alice" and n2 == "Bob"


# --- engine units ----------------------------------------------------------

def test_save_id_sanitized():
    from core.generative_save import GenerativeSave, saves_dir
    from pathlib import Path
    p = GenerativeSave._save_path("../../etc/passwd")
    assert p.name == "etcpasswd.json"
    assert p.resolve().parent == saves_dir().resolve()


def test_rel_type_whitelist():
    from core.entity_graph import EntityGraph
    g = EntityGraph.__new__(EntityGraph)
    g.enabled = False
    assert g.add_relationship("a", "EVIL_INJECT", "b") is False


def test_failure_consequence_scales():
    from core.game_generative import GenerativeGameEngine
    from core.archetypes import create_investigator
    e = GenerativeGameEngine(model="mistral", use_memory=False, session_id="u")
    e.create_game(create_investigator("T", "scholar"))
    small = e._failure_consequence({"skill": "climb", "roll": 55, "target": 50})
    fumble = e._failure_consequence({"skill": "climb", "roll": 99, "target": 50})
    assert small["kind"] == "hp" and fumble["fumble"] and fumble["amount"] >= small["amount"]


def test_ammo_and_firearm():
    from core.game_generative import GenerativeGameEngine
    from core.archetypes import create_investigator
    e = GenerativeGameEngine(model="mistral", use_memory=False, session_id="u2")
    e.create_game(create_investigator("T", "scholar"))
    assert e.state.ammo == 0 and e.resources_status()["has_firearm"] is False
    e.state.location = e.adventure_config.item_locations["revolver"]
    e.pick_up_item("revolver")
    assert e.state.ammo > 0 and e.resources_status()["has_firearm"] is True


def test_location_needs_movement():
    from core.game_generative import GenerativeGameEngine
    from core.archetypes import create_investigator
    from unittest.mock import patch
    e = GenerativeGameEngine(model="mistral", use_memory=False, session_id="u3")
    e.create_game(create_investigator("T", "scholar"))
    start = e.state.location
    with patch.object(e, "_call_ollama", return_value="You wonder about the hidden chamber above."):
        e.process_player_action("what is up there?")
    assert e.state.location == start  # mere mention must not teleport


# --- admin dashboard -------------------------------------------------------
# The only two endpoints with access control, and they had no coverage at all.
# Everything here is about the gate, not the numbers behind it.

def _admin_app(tmp_path, **cfg):
    import app as app_module
    return app_module.create_app({"DATA_DIR": str(tmp_path), **cfg}).test_client()


def test_admin_disabled_when_no_token_configured(tmp_path):
    """With ADMIN_TOKEN unset the dashboard must be closed, not open.

    `_admin_authorized` leads with `bool(ADMIN_TOKEN)`; if that guard were ever
    dropped, an empty configured token would compare equal to an empty query
    token and the dashboard would be world-readable.
    """
    c = _admin_app(tmp_path, ADMIN_TOKEN="")
    assert c.get("/admin").status_code == 401
    assert c.get("/admin?token=").status_code == 401
    assert c.get("/api/admin/stats?token=").status_code == 401
    assert c.get("/api/admin/stats").status_code == 401


def test_admin_rejects_wrong_token(tmp_path):
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret")
    for bad in ("", "wrong", "s3cre", "s3secret", "S3CRET", "s3cret "):
        assert c.get(f"/api/admin/stats?token={bad}").status_code == 401, bad
        assert c.get(f"/admin?token={bad}").status_code == 401, bad
    assert c.get("/api/admin/stats").status_code == 401


def test_admin_accepts_correct_token(tmp_path):
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret")

    r = c.get("/api/admin/stats?token=s3cret")
    assert r.status_code == 200
    body = r.get_json()
    for key in ("active_sessions", "total_saves", "players", "played",
                "opened_only", "feedback_count", "sessions", "feedback"):
        assert key in body, key

    page = c.get("/admin?token=s3cret")
    assert page.status_code == 200
    assert b"Unauthorized" not in page.data


def test_admin_unauthorized_page_explains_how(tmp_path):
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret")
    r = c.get("/admin")
    assert r.status_code == 401
    assert b"token" in r.data.lower()


def test_admin_stats_excludes_configured_names(tmp_path):
    """EXCLUDE_NAMES keeps the team's own sessions out of the playtest numbers."""
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret", EXCLUDE_NAMES="Adrian, tester")

    saves = tmp_path / "saves" / "generative"
    saves.mkdir(parents=True)
    import json as _j

    def _save(name, actions):
        (saves / f"{name}.json").write_text(_j.dumps({
            "game_state": {
                "investigator": {"name": name, "characteristics": {"SAN": 60, "HP": 9}},
                "narrative": [f"Player: act {i}" for i in range(actions)],
                "turn": actions,
                "location": "Point Black Lighthouse - Exterior",
            }
        }))

    _save("Adrian", 5)      # excluded by name
    _save("tester", 3)      # excluded by name, case-insensitively
    _save("Pao", 4)         # counted, and played
    _save("Champi", 0)      # counted, opened only

    body = c.get("/api/admin/stats?token=s3cret").get_json()
    assert body["total_saves"] == 4          # every file is seen
    assert body["players"] == 2              # but only non-excluded ones count
    assert body["played"] == 1
    assert body["opened_only"] == 1
    names = {s["name"] for s in body["sessions"]}
    assert names == {"Pao", "Champi"}


def test_admin_stats_reports_playtest_telemetry(tmp_path):
    """The dashboard must separate an unreachable mechanic from an unfound one.

    Two saves, two different failures — the same "0 rolls thrown" on the
    surface, opposite causes underneath.
    """
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret")
    saves = tmp_path / "saves" / "generative"
    saves.mkdir(parents=True)
    import json as _j

    def _save(name, actions, telemetry):
        (saves / f"{name}.json").write_text(_j.dumps({
            "game_state": {
                "investigator": {"name": name, "characteristics": {"SAN": 60, "HP": 9}},
                "narrative": [f"Player: act {i}" for i in range(actions)],
                "turn": actions,
                "location": "Point Black Lighthouse - Exterior",
                "telemetry": telemetry,
            }
        }))

    # Nothing ever asked for a roll: the matcher never fired.
    _save("angelin", 29, {"actions": 29, "rolls_from_dm": 0,
                          "rolls_synthesized": 0, "rolls_thrown": 0})
    # Dice were offered repeatedly and never thrown: the die is not findable.
    _save("champi", 12, {"actions": 12, "rolls_from_dm": 4,
                         "rolls_synthesized": 0, "rolls_thrown": 0})
    # A session that works, so the roll-ups are not trivially zero.
    _save("pao", 13, {"actions": 13, "rolls_from_dm": 3,
                      "rolls_synthesized": 2, "rolls_thrown": 4})

    t = c.get("/api/admin/stats?token=s3cret").get_json()["telemetry"]

    assert t["sessions_mechanic_silent"] == 1        # angelin only
    assert t["sessions_dice_undiscovered"] == 1      # champi only
    assert t["sessions_with_rolls_offered"] == 2
    assert t["rolls_offered"] == 9                   # 4 + 3 + 2
    assert t["rolls_thrown"] == 4
    assert t["throw_rate"] == round(4 / 9, 2)
    assert t["dm_roll_compliance"] == round(7 / 9, 2)


def test_admin_stats_telemetry_handles_saves_without_it(tmp_path):
    """Saves written before telemetry existed must not break the dashboard."""
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret")
    saves = tmp_path / "saves" / "generative"
    saves.mkdir(parents=True)
    import json as _j
    (saves / "old.json").write_text(_j.dumps({
        "game_state": {
            "investigator": {"name": "Old", "characteristics": {"SAN": 55, "HP": 8}},
            "narrative": ["Player: look around"],
            "turn": 1,
            "location": "Point Black Lighthouse - Exterior",
        }
    }))

    r = c.get("/api/admin/stats?token=s3cret")
    assert r.status_code == 200
    t = r.get_json()["telemetry"]
    assert t["rolls_offered"] == 0
    assert t["throw_rate"] is None          # no division by zero
    assert t["dm_roll_compliance"] is None


# --- endpoints that had no coverage ----------------------------------------
# 8 of 16 routes were never exercised by a test. These close that gap before
# app.py is refactored, so the refactor has a net under it — the last two
# refactors of this file shipped three regressions between them.

def test_index_serves_the_game_shell(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"action-input" in r.data          # the game actually renders


def test_health_reports_session_count(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert isinstance(body["sessions"], int)


def test_archetypes_expose_playable_sheets(client):
    r = client.get("/api/archetypes")
    assert r.status_code == 200
    arch = r.get_json()["archetypes"]
    assert {"scholar", "detective", "occultist", "wanderer"} <= set(arch)
    scholar = arch["scholar"]
    # The startup screen previews stats and skills from this payload.
    assert scholar["characteristics"]["INT"] > 0
    assert scholar["skills"]


def test_saves_empty_then_populated(client):
    assert client.get("/api/game/saves").get_json()["saves"] == []
    _start(client)
    client.post("/api/game/action", json={"action": "look around"})
    saves = client.get("/api/game/saves").get_json()["saves"]
    assert len(saves) == 1
    assert saves[0]["investigator"] == "Tester"


def test_load_without_a_save_is_404(client):
    assert client.post("/api/game/load").status_code == 404


def test_load_resumes_the_autosave(client):
    _start(client)
    client.post("/api/game/action", json={"action": "look around"})
    before = client.get("/api/game/state").get_json()

    r = client.post("/api/game/load")
    assert r.status_code == 200
    body = r.get_json()
    assert body["success"]
    assert body["turn"] == before["turn"]
    assert body["location"] == before["location"]
    assert body["state"]["HP"] > 0


def test_flee_requires_a_game_and_a_fight(client):
    assert client.post("/api/game/flee").status_code == 400   # no game
    _start(client)
    r = client.post("/api/game/flee")
    assert r.status_code == 400                                # not in combat
    assert "combat" in r.get_json()["error"].lower()


def test_flee_breaks_off_combat(tmp_path):
    """Start a real fight through the DM, then break off through the API."""
    fight = "A shape rises from the water. [COMBAT_START: deep_one_hybrid]"

    def fake_chat(self, *a, **k):
        if k.get("on_chunk"):
            k["on_chunk"](fight)
        return fight

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        c = _make_app(tmp_path).test_client()
        c.post("/api/game/start", json={"name": "Runner", "archetype": "scholar"})
        turn = c.post("/api/game/action", json={"action": "approach the water"}).get_json()
        assert turn["combat"] is not None, "the fight never started"

        r = c.post("/api/game/flee")
        assert r.status_code == 200, r.get_data(as_text=True)
        body = r.get_json()
        assert body["success"]
        assert body["combat"] is None      # the fight is over

        # And it stays over: fleeing twice is refused, not a second escape.
        assert c.post("/api/game/flee").status_code == 400


def test_feedback_validates_input(client):
    _start(client)
    assert client.post("/api/feedback", json={"text": "   "}).status_code == 400
    assert client.post("/api/feedback", json={}).status_code == 400
    assert client.post("/api/feedback", json={"text": "x" * 2001}).status_code == 413


def test_feedback_is_stored_and_reaches_admin(tmp_path):
    """Feedback must survive to the dashboard — it is the only qualitative signal."""
    import app as app_module
    app_obj = app_module.create_app({"DATA_DIR": str(tmp_path), "ADMIN_TOKEN": "s3cret"})
    c = app_obj.test_client()
    with patch("core.llm_client.LLMClient.chat", lambda self, *a, **k: CANNED_DM), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        c.post("/api/game/start", json={"name": "Rater", "archetype": "scholar"})
        r = c.post("/api/feedback", json={"text": "está chulo", "rating": 5})
    assert r.status_code == 200 and r.get_json()["success"]

    body = c.get("/api/admin/stats?token=s3cret").get_json()
    assert body["feedback_count"] == 1
    assert body["avg_rating"] == 5
    entry = body["feedback"][0]
    assert entry["text"] == "está chulo"
    assert entry["investigator"] == "Rater"


def test_feedback_rating_out_of_range_is_dropped_not_stored(tmp_path):
    import app as app_module
    c = app_module.create_app({"DATA_DIR": str(tmp_path), "ADMIN_TOKEN": "s3cret"}).test_client()
    assert c.post("/api/feedback", json={"text": "ok", "rating": 99}).status_code == 200
    body = c.get("/api/admin/stats?token=s3cret").get_json()
    assert body["feedback"][0]["rating"] is None
    assert body["avg_rating"] is None


def test_images_reject_traversal(client):
    """The image route joins a user-controlled path — traversal must not escape."""
    for attack in ("../../etc/passwd", "..%2f..%2fetc%2fpasswd", "....//etc/passwd"):
        r = client.get(f"/images/{attack}")
        assert r.status_code in (400, 403, 404), (attack, r.status_code)
        assert b"root:" not in r.data


def test_images_missing_file_is_404(client):
    assert client.get("/images/nope.png").status_code == 404


def test_rate_limit_returns_429(tmp_path):
    """Six starts a minute is the configured budget; the seventh must be refused."""
    import app as app_module
    c = app_module.create_app({"DATA_DIR": str(tmp_path)}).test_client()
    with patch("core.llm_client.LLMClient.chat", lambda self, *a, **k: CANNED_DM), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        codes = [c.post("/api/game/start",
                        json={"name": "Flood", "archetype": "scholar"}).status_code
                 for _ in range(8)]
    assert 429 in codes, codes
    assert codes.index(429) >= 6, codes    # the budget is spent first, not early


def test_state_reports_active_combat(tmp_path):
    """/api/game/state must carry combat, or the HUD dies on every refresh.

    The client calls renderCombat(data.combat) from refreshGameState(), which
    runs right after each turn. With combat absent from the payload that is
    renderCombat(undefined) — it hides the combat bar and stops the combat
    music one tick after the turn showed them, and a page reload mid-fight
    shows no fight at all while the engine still has an enemy active.
    """
    fight = "A shape rises from the water. [COMBAT_START: deep_one_hybrid]"

    def fake_chat(self, *a, **k):
        if k.get("on_chunk"):
            k["on_chunk"](fight)
        return fight

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        c = _make_app(tmp_path).test_client()
        c.post("/api/game/start", json={"name": "Fighter", "archetype": "scholar"})
        turn = c.post("/api/game/action", json={"action": "approach the water"}).get_json()
        assert turn["combat"] is not None

        state = c.get("/api/game/state").get_json()
        assert state.get("combat") is not None, "combat missing from state"
        assert state["combat"]["name"] == turn["combat"]["name"]

        c.post("/api/game/flee")
        assert c.get("/api/game/state").get_json()["combat"] is None


def test_health_surfaces_a_degraded_model(client):
    """/api/health must not report ok while the model is answering nothing."""
    from core.llm_client import LLMClient

    assert client.get("/api/health").get_json()["status"] == "ok"

    before = LLMClient.degraded_turns
    try:
        LLMClient._degrade("model_not_found", LLMClient.GENERIC_FALLBACK)
        body = client.get("/api/health").get_json()
        assert body["status"] == "degraded"
        assert body["llm"]["degraded_turns"] > 0
        assert body["llm"]["last_error"] == "model_not_found"
    finally:
        LLMClient.degraded_turns = before
        LLMClient.last_error = None


# --- persistence isolation (MAGI #42) ----------------------------------------

def test_saves_and_playtests_follow_the_configured_data_dir(tmp_path, monkeypatch):
    """The app's DATA_DIR (Flask config) must govern the engine's saves and
    playtest archives too. Before #42 they read only the env var, defaulting
    to the repo root: every test run left fixture games in saves/ and
    playtests/, and the analyzer reported them as players dying at turn 2."""
    import os
    from pathlib import Path
    monkeypatch.delenv("DATA_DIR", raising=False)             # the leaky default
    repo = Path(__file__).resolve().parent.parent
    before_saves = set((repo / "saves" / "generative").glob("*.json")) \
        if (repo / "saves" / "generative").exists() else set()
    before_pt = set((repo / "playtests").glob("*.json")) if (repo / "playtests").exists() else set()

    def fake_chat(self, *a, **k):
        on = k.get("on_chunk")
        if on:
            on(CANNED_DM)
        return CANNED_DM

    def fake_tools(self, *a, **k):
        return {"narrative": "", "tool_calls": [], "fallback": True}

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools", fake_tools):
        c = _make_app(tmp_path).test_client()
        _start(c)
        assert c.post("/api/game/action", json={"action": "look around"}).status_code == 200
        assert c.post("/api/game/reset").get_json()["success"]

    # reset archives the run under the configured dir (and deletes its save)
    assert len(list((tmp_path / "playtests").glob("*.json"))) == 1
    after_saves = set((repo / "saves" / "generative").glob("*.json")) \
        if (repo / "saves" / "generative").exists() else set()
    after_pt = set((repo / "playtests").glob("*.json")) if (repo / "playtests").exists() else set()
    assert after_saves == before_saves and after_pt == before_pt              # nothing leaked


def test_two_apps_in_one_process_keep_separate_data_dirs(tmp_path):
    """web/__init__ promises two apps per process with separate state; #43
    (balthasar) asked for proof that persistence honors it too — a
    process-wide DATA_DIR override would have sent both apps' saves and
    playtest archives to whichever app was created last."""
    import json
    a_dir, b_dir = tmp_path / "a", tmp_path / "b"

    def fake_chat(self, *a, **k):
        on = k.get("on_chunk")
        if on:
            on(CANNED_DM)
        return CANNED_DM

    def fake_tools(self, *a, **k):
        return {"narrative": "", "tool_calls": [], "fallback": True}

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools", fake_tools):
        a = _make_app(a_dir).test_client()
        b = _make_app(b_dir).test_client()          # created last: must not capture A
        _start(a, name="Alpha")
        _start(b, name="Beta")
        assert a.post("/api/game/action", json={"action": "look around"}).status_code == 200
        assert b.post("/api/game/reset").get_json()["success"]

    a_saves = list((a_dir / "saves" / "generative").glob("*.json"))
    b_saves = list((b_dir / "saves" / "generative").glob("*.json"))
    assert len(a_saves) == 1 and json.loads(a_saves[0].read_text(encoding="utf-8"))["metadata"]["investigator"] == "Alpha"
    assert b_saves == []                                          # reset deleted B's save
    assert not (a_dir / "playtests").exists()                     # A never reset
    assert len(list((b_dir / "playtests").glob("*.json"))) == 1   # B's archive, under B
