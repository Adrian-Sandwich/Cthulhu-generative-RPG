"""Opt-in request timings. Never collect prompts, cookies, URLs or credentials."""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import json
import logging
import os
import threading
from time import perf_counter
from uuid import uuid4

_current = ContextVar('request_timing', default=None)
logger = logging.getLogger('cthulhu.timing')


@contextmanager
def measure(name):
    trace = _current.get()
    if trace is None:
        yield
        return
    started = perf_counter()
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        with trace['lock']:
            value = trace['spans'].setdefault(name, {'seconds': 0, 'calls': 0, 'errors': 0})
            value['seconds'] += perf_counter() - started
            value['calls'] += 1
            value['errors'] += int(failed)


def timed(name):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with measure(name):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def log_record(record):
    logger.info(json.dumps(record, separators=(',', ':')))


class TimingMiddleware:
    """Measures WSGI execution and iteration, including close after disconnect.

    Does not measure the server's queue before invoking WSGI. A private sink is
    injectable for tests/load runs; production uses one JSON log per request.
    """
    def __init__(self, app, sink=log_record):
        self.app, self.sink = app, sink

    def __call__(self, environ, start_response):
        trace = {'request_id': uuid4().hex, 'spans': {}, 'lock': threading.Lock()}
        started = perf_counter()
        status_code = 500
        finished = False

        def finish(outcome):
            nonlocal finished
            if finished:
                return
            finished = True
            record = {'event': 'request_timing', 'request_id': trace['request_id'],
                      'pid': os.getpid(), 'route': environ.get('cthulhu.route', '<unmatched>'),
                      'status': status_code, 'outcome': outcome,
                      'seconds': round(perf_counter() - started, 6),
                      'spans': {key: dict(value, seconds=round(value['seconds'], 6))
                                for key, value in trace['spans'].items()}}
            try:
                self.sink(record)
            except Exception:
                # An observability sink must not break gameplay.
                logger.warning('Request timing sink failed')

        def respond(status, headers, exc_info=None):
            nonlocal status_code
            status_code = int(status.split()[0])
            return start_response(status, headers + [('X-Request-ID', trace['request_id'])], exc_info)

        token = _current.set(trace)
        try:
            iterable = self.app(environ, respond)
            iterator = iter(iterable)
        except BaseException:
            finish('exception')
            raise
        finally:
            _current.reset(token)

        class Body:
            def __iter__(self):
                return self

            def __next__(self):
                token = _current.set(trace)
                try:
                    return next(iterator)
                except StopIteration:
                    finish('exhausted')
                    raise
                except BaseException:
                    finish('exception')
                    raise
                finally:
                    _current.reset(token)

            def close(self):
                token = _current.set(trace)
                try:
                    if hasattr(iterable, 'close'):
                        iterable.close()
                finally:
                    finish('closed')
                    _current.reset(token)

        return Body()
