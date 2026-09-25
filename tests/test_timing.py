import json
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

import pytest

from core.timing import TimingMiddleware, measure, _current


def invoke(app, sink):
    headers = []
    body = TimingMiddleware(app, sink)(
        {'cthulhu.route': '/api/game/actions/<action_id>', 'QUERY_STRING': 'token=secret'},
        lambda status, values, exc_info=None: headers.extend(values))
    return body, headers


def test_stream_keeps_thread_spans_and_never_collects_query_or_body():
    records = []

    def app(environ, respond):
        respond('200 OK', [])
        def generate():
            def work():
                with measure('llm.chat'):
                    pass
            with ThreadPoolExecutor(1) as executor:
                executor.submit(copy_context().run, work).result()
            yield b'private narrative'
        return generate()

    body, headers = invoke(app, records.append)
    assert not records and _current.get() is None
    assert list(body) == [b'private narrative']
    body.close()
    assert _current.get() is None
    assert len(records) == 1
    record = records[0]
    assert record['spans']['llm.chat']['calls'] == 1
    assert record['outcome'] == 'exhausted'
    assert dict(headers)['X-Request-ID'] == record['request_id']
    assert 'secret' not in json.dumps(record) and 'private narrative' not in json.dumps(record)


def test_disconnect_records_cleanup_and_restores_context():
    records = []
    def app(environ, respond):
        respond('200 OK', [])
        def generate():
            try:
                yield b'first'
                yield b'second'
            finally:
                with measure('cleanup'):
                    pass
        return generate()
    body, _ = invoke(app, records.append)
    next(body)
    body.close()
    body.close()
    assert len(records) == 1
    assert records[0]['outcome'] == 'closed'
    assert records[0]['spans']['cleanup']['calls'] == 1
    assert _current.get() is None


def test_error_is_recorded_and_failing_sink_does_not_mask_it():
    records = []
    def sink(record):
        records.append(record)
        raise RuntimeError('sink failed')
    def app(environ, respond):
        with measure('postgres.connect'):
            raise ValueError('original failure')
    with pytest.raises(ValueError, match='original failure'):
        invoke(app, sink)
    assert records[0]['spans']['postgres.connect']['errors'] == 1
    assert records[0]['outcome'] == 'exception'
    assert _current.get() is None


def test_requests_are_isolated_and_unmatched_path_is_not_logged(tmp_path):
    from app import create_app
    records = []
    app = create_app({'DATA_DIR': str(tmp_path), 'REQUEST_TIMING': True, 'TIMING_SINK': records.append})
    client = app.test_client()
    for _ in range(2):
        response = client.get('/private-user-input?token=secret', buffered=True)
        response.close()
    assert len(records) == 2
    assert records[0]['request_id'] != records[1]['request_id']
    assert all(r['route'] == '<unmatched>' and r['status'] == 404 for r in records)
    assert 'private-user-input' not in json.dumps(records)


def test_disabled_by_default(tmp_path):
    from app import create_app
    app = create_app({'DATA_DIR': str(tmp_path), 'REQUEST_TIMING': False})
    response = app.test_client().get('/api/health')
    assert 'X-Request-ID' not in response.headers
