"""Measurement contracts: errors must not disappear inside latency averages."""

from tools.load_test import percentile, summarize, stream_turn, summarize_timings


def test_percentiles_use_nearest_rank_and_empty_is_not_zero():
    assert percentile([], 95) is None
    assert percentile([4, 1, 3, 2], 50) == 2
    assert percentile([4, 1, 3, 2], 95) == 4


def test_server_residual_pairs_requests_instead_of_subtracting_percentiles():
    records = [
        {'request_id': 'a', 'seconds': 10, 'spans': {'llm.chat': {'seconds': 8}}},
        {'request_id': 'b', 'seconds': 1, 'spans': {}},
    ]
    samples = [{'request_id': 'b', 'seconds': 5}, {'request_id': 'a', 'seconds': 11},
               {'request_id': 'missing', 'seconds': 100}]
    result = summarize_timings(records, samples)
    assert result['paired_records'] == 2
    assert result['seconds']['outside_wsgi']['p95'] == 4
    assert result['seconds']['llm.chat']['p95'] == 8


def test_failed_turns_are_counted_but_not_success_latency():
    samples = [
        {'outcome': 'ok', 'seconds': 2, 'first_text_seconds': 0.2},
        {'outcome': 'ok', 'seconds': 4, 'first_text_seconds': 0.4},
        {'outcome': 'http_503', 'seconds': 10, 'first_text_seconds': None},
    ]
    result = summarize(samples, 20)
    assert result['attempted'] == 3 and result['completed'] == 2
    assert result['completed_per_second'] == 0.1
    assert result['completion_seconds']['p95'] == 4
    assert result['outcomes']['http_503'] == 1


def test_sse_error_is_not_counted_as_http_200_success():
    class Response:
        status_code = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def iter_lines(self, chunk_size):
            yield from [b'event: error', b'data: {"error":"failure"}', b'']
    class Session:
        def post(self, *args, **kwargs):
            return Response()
    sample, payload = stream_turn(Session(), 'http://test', {}, 1)
    assert sample['outcome'] == 'sse_error'
    assert payload is None


def test_stream_without_terminal_event_is_incomplete():
    class Response:
        status_code = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def iter_lines(self, chunk_size):
            yield from [b'data: {"chunk":"partial text"}', b'']
    class Session:
        def post(self, *args, **kwargs):
            return Response()
    sample, payload = stream_turn(Session(), 'http://test', {}, 1)
    assert sample['outcome'] == 'incomplete'
    assert sample['first_text_seconds'] is not None
