import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from core import llm_client as llm


@pytest.fixture
def endpoint(monkeypatch):
    entry = {'url': 'http://test', 'model': None, 'inflight': 0, 'max': 1, 'down_until': 0}
    monkeypatch.setattr(llm, '_POOL', [entry])
    monkeypatch.setenv('LLM_QUEUE_TIMEOUT', '0.05')
    return entry


def test_saturated_endpoint_never_overcommits_and_release_wakes_waiter(endpoint, monkeypatch):
    monkeypatch.setenv('LLM_QUEUE_TIMEOUT', '2')
    held = llm._acquire_endpoint()
    started = threading.Event()
    def wait():
        started.set()
        return llm._acquire_endpoint()
    with ThreadPoolExecutor(1) as executor:
        future = executor.submit(wait)
        assert started.wait(1)
        assert not future.done() and endpoint['inflight'] == 1
        llm._release_endpoint(held, True)
        assert future.result(timeout=1) is endpoint
        assert endpoint['inflight'] == 1
        llm._release_endpoint(endpoint, True)


@pytest.mark.parametrize('tools', [False, True])
def test_admission_timeout_sends_no_request(endpoint, monkeypatch, tools):
    endpoint['inflight'] = 1
    monkeypatch.setattr(llm.requests, 'post', lambda *a, **k: pytest.fail('capacity bypass'))
    client = llm.LLMClient()
    result = client.chat_with_tools([], []) if tools else client.chat([])
    assert result['fallback'] if tools else result == client.NETWORK_FALLBACK
    assert endpoint['inflight'] == 1


@pytest.mark.parametrize('tools', [False, True])
def test_cancellation_returns_permit(endpoint, monkeypatch, tools):
    def cancel(*args, **kwargs):
        raise KeyboardInterrupt()
    monkeypatch.setattr(llm.requests, 'post', cancel)
    client = llm.LLMClient()
    with pytest.raises(KeyboardInterrupt):
        client.chat_with_tools([], []) if tools else client.chat([])
    assert endpoint['inflight'] == 0
