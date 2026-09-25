"""Isolated HTTP load test: real WSGI processes + PostgreSQL, simulated LLM.

Set CTHULHU_TEST_DATABASE_URL to a disposable database. No production server
is contacted. --live-model explicitly enables the configured LLM provider.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime, timezone
import json
import logging
import math
import multiprocessing
import os
from pathlib import Path
import platform
import secrets
import sys
import tempfile
import threading
import time
from unittest.mock import patch
from uuid import uuid4

import psutil
import requests
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.postgres_store import PostgresStore
from core.timing import timed


def percentile(values, percentile_value):
    if not values:
        return None
    values = sorted(values)
    return round(values[max(0, math.ceil(len(values) * percentile_value / 100) - 1)], 4)


def summarize(samples, elapsed):
    passed = [sample for sample in samples if sample['outcome'] == 'ok']
    durations = [sample['seconds'] for sample in passed]
    first_text = [sample['first_text_seconds'] for sample in passed if sample.get('first_text_seconds') is not None]
    return {
        'attempted': len(samples), 'completed': len(passed),
        'outcomes': dict(Counter(sample['outcome'] for sample in samples)),
        'elapsed_seconds': round(elapsed, 4),
        'completed_per_second': round(len(passed) / elapsed, 3) if elapsed else 0,
        'completion_seconds': {f'p{p}': percentile(durations, p) for p in (50, 95, 99)},
        'first_text_seconds': {f'p{p}': percentile(first_text, p) for p in (50, 95, 99)},
    }


def _serve(config, ready, generations):
    # Isolate module-level app initialization and optional subsystems too.
    os.environ.update(DATA_DIR=config['data_dir'], CTHULHU_DATABASE_URL='',
                      WEB_CONCURRENCY='1', MODERATION='local', ENABLE_ENTITY_GRAPH='0', ENABLE_IMAGES='0')
    logging.basicConfig(level=logging.ERROR)
    from app import create_app
    from core.llm_client import LLMClient
    from waitress import create_server

    @timed('llm.chat')
    def simulated_chat(self, *args, **kwargs):
        with generations.get_lock():
            generations.value += 1
        pieces = ['The wind moves ', 'across the water. ', 'A light flickers ', 'in the distance.']
        for piece in pieces:
            time.sleep(config['model_seconds'] / len(pieces))
            if kwargs.get('on_chunk'):
                kwargs['on_chunk'](piece)
        return ''.join(pieces)

    with ExitStack() as stack:
        if not config['live_model']:
            stack.enter_context(patch.object(LLMClient, 'chat', simulated_chat))
            stack.enter_context(patch.object(LLMClient, 'chat_with_tools', return_value={
                'narrative': '', 'tool_calls': [], 'fallback': True,
            }))
        timing_lock = threading.Lock()

        def timing_sink(record):
            with timing_lock:
                with open(config['timing_file'], 'a', encoding='utf-8') as output:
                    output.write(json.dumps(record) + '\n')

        app = create_app({'DATABASE_URL': config['dsn'], 'DATABASE_SCHEMA': config['schema'],
                          'SECRET_KEY': config['secret'], 'DATA_DIR': config['data_dir'],
                          'PG_POOL_SIZE': config['pg_pool_size'],
                          'REQUEST_TIMING': config['request_timing'], 'TIMING_SINK': timing_sink})
        if config['profile'] == 'capacity':
            # The generator uses a single loopback IP. Raise budgets ONLY in
            # this disposable app, never in production or the guardrail run.
            game = app.extensions['cthulhu']
            game.RATE_LIMITS = {bucket: (1000000, window) for bucket, (_, window) in game.RATE_LIMITS.items()}
        server = create_server(app, host='127.0.0.1', port=0, threads=config['threads'])
        ready.put((os.getpid(), server.effective_port))
        server.run()


def stream_turn(session, url, command, timeout):
    started = time.perf_counter()
    sample = {'outcome': 'incomplete', 'seconds': 0, 'first_text_seconds': None}
    payload = None
    try:
        with session.post(url + '/api/game/action/stream', json=command,
                          stream=True, timeout=(5, timeout)) as response:
            sample['request_id'] = getattr(response, 'headers', {}).get('X-Request-ID')
            if response.status_code != 200:
                sample['outcome'] = f'http_{response.status_code}'
            else:
                event, data = 'message', []
                # Small chunks avoid Requests buffering short SSE frames and
                # falsely reporting model-completion time as first text time.
                for line in response.iter_lines(chunk_size=1):
                    line = line.decode('utf-8')
                    if line.startswith('event:'):
                        event = line[6:].strip()
                    elif line.startswith('data:'):
                        data.append(line[5:].strip())
                    elif not line and data:
                        frame = json.loads('\n'.join(data))
                        if event == 'done':
                            payload = frame
                            sample['outcome'] = 'ok' if frame.get('success') else 'invalid_result'
                        elif event == 'error':
                            sample['outcome'] = 'sse_error'
                        elif frame.get('chunk') and sample['first_text_seconds'] is None:
                            sample['first_text_seconds'] = time.perf_counter() - started
                        event, data = 'message', []
    except (requests.RequestException, ValueError) as exc:
        sample['outcome'] = type(exc).__name__
    sample['seconds'] = round(time.perf_counter() - started, 4)
    return sample, payload


def run_stage(urls, users, turns, timeout, request_timing=False):
    sessions, samples, setup, violations = [], [], [], []

    def start(index):
        session = requests.Session()
        session.trust_env = False
        try:
            response = session.post(urls[index % len(urls)] + '/api/game/start',
                                    json={'name': f'Load-{index}', 'archetype': 'scholar'}, timeout=(5, timeout))
            if response.status_code != 200:
                session.close()
                return None, f'http_{response.status_code}'
            return (session, response.json()['game_id'], index), 'ok'
        except (requests.RequestException, ValueError, KeyError) as exc:
            session.close()
            return None, type(exc).__name__

    with ThreadPoolExecutor(max_workers=users) as pool:
        for value, outcome in pool.map(start, range(users)):
            setup.append(outcome)
            if value:
                sessions.append(value)

    barrier = threading.Barrier(len(sessions)) if sessions else None

    def player(item):
        session, game_id, index = item
        local, errors = [], []
        completed = 0
        try:
            barrier.wait(timeout=timeout)
            for turn in range(turns):
                command = {'action': 'I wait quietly.', 'action_id': uuid4().hex, 'game_id': game_id}
                node = (index + turn) % len(urls)
                sample, result = stream_turn(session, urls[node], command, timeout)
                local.append(sample)
                if sample['outcome'] != 'ok':
                    break
                completed += 1
                if result.get('action_id') != command['action_id']:
                    errors.append('wrong_action_id')
                # Once per player, exercise replay on another server. Never
                # replay failed/ambiguous requests in this latency measurement.
                if turn == 0:
                    other = urls[(node + 1) % len(urls)]
                    replay = session.post(other + '/api/game/action', json=command, timeout=(5, timeout))
                    if replay.status_code != 200 or replay.json() != result:
                        errors.append('replay_mismatch')
                    receipt = session.get(other + '/api/game/actions/' + command['action_id'], timeout=(5, timeout))
                    if receipt.status_code != 200 or receipt.json().get('status') != 'completed':
                        errors.append('receipt_mismatch')
                if result.get('pending_roll'):
                    roll = session.post(urls[node] + '/api/game/roll', timeout=(5, timeout))
                    if roll.status_code != 200:
                        errors.append('roll_failed')
                        break
                if result.get('ending'):
                    # A real model may finish a game; report the shorter run.
                    break
            state = session.get(urls[(index + 1) % len(urls)] + '/api/game/state', timeout=(5, timeout))
            if state.status_code != 200 or state.json().get('turn') != 1 + completed:
                errors.append('turn_count_mismatch')
        except (requests.RequestException, ValueError, KeyError, threading.BrokenBarrierError) as exc:
            errors.append(type(exc).__name__)
        finally:
            session.close()
        return local, errors

    started = time.perf_counter()
    if sessions:
        with ThreadPoolExecutor(max_workers=len(sessions)) as pool:
            for local, errors in pool.map(player, sessions):
                samples.extend(local)
                violations.extend(errors)
    result = summarize(samples, time.perf_counter() - started)
    result.update(users=users, admitted=len(sessions), requested_turns=users * turns,
                  setup_outcomes=dict(Counter(setup)), verification_errors=dict(Counter(violations)))
    if request_timing:
        result['client_samples'] = samples
    return result


def markdown_report(report):
    lines = ['# Local load test', '',
             f"UTC: {report['timestamp']}", '',
             f"Profile: {report['profile']}; model: {report['model']}; "
             f"servers: {report['workers']}; threads/server: {report['threads']}; "
             f"simulated generation: {report['model_seconds']} s.", '',
             f"Short-operation PostgreSQL pool size per server: {report.get('pg_pool_size', 'not recorded')}.", '',
             'Real HTTP + PostgreSQL. Closed-loop clients, no think time. '
             'Setup excluded from stage timing; cross-server verification included in throughput. '
             'Latency percentiles include successful streaming turns only.', '',
             '| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |',
             '|---:|---:|---:|---:|---:|---:|---|']
    for stage in report['stages']:
        errors = {k: v for k, v in stage['outcomes'].items() if k != 'ok'}
        lines.append(f"| {stage['users']} | {stage['admitted']} | {stage['completed']}/{stage['attempted']} | "
                     f"{stage['completed_per_second']} | {stage['first_text_seconds']['p95']} | "
                     f"{stage['completion_seconds']['p95']} | {errors or '-'} |")
    if report.get('request_timing'):
        lines += ['', '## Server timing (stream requests only)', '',
                  'Seconds per request, p95; nested spans overlap and must not be added. '
                  'WSGI duration excludes the HTTP server queue before invocation.', '',
                  '| Clients | Records | WSGI | PG connect | PG pool wait | PG session lock | PG read | PG write | LLM chat | Outside WSGI |',
                  '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for stage in report['stages']:
            timing = stage['server_timing']
            fields = ['wsgi', 'postgres.connect', 'postgres.pool_wait', 'postgres.session_lock', 'postgres.read',
                      'postgres.write', 'llm.chat', 'outside_wsgi']
            values = ' | '.join(str(timing['seconds'].get(field, {}).get('p95', 'not recorded')) for field in fields)
            lines.append(f"| {stage['users']} | {timing['records']} | {values} |")
    lines += ['', f"Database audit: `{json.dumps(report['audit'])}`", '',
              f"Worker resource samples: `{json.dumps(report['resources'])}`", '',
              'These local results do not establish production capacity. The client, app and database '
              'share this machine; the WSGI server is Waitress, not production Gunicorn. '
              'Capacity mode raises rate-limit budgets only in the isolated harness. '
              'Guardrails mode keeps normal limits and all clients share one IP.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--levels', default='1,8,16,32,64')
    parser.add_argument('--turns', type=int, default=4)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--threads', type=int, default=16)
    parser.add_argument('--model-seconds', type=float, default=0.5)
    parser.add_argument('--timeout', type=float, default=45)
    parser.add_argument('--profile', choices=['capacity', 'guardrails'], default='capacity')
    parser.add_argument('--live-model', action='store_true', help='Explicitly allow configured LLM API calls/costs')
    parser.add_argument('--request-timing', action='store_true', help='Save per-request server timings as JSONL')
    parser.add_argument('--pg-pool-size', type=int, default=4, help='Short-operation connections per worker; 0 disables reuse')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    levels = [int(value) for value in args.levels.split(',')]
    if min(levels + [args.turns, args.workers, args.threads]) < 1 or max(levels) > 256:
        parser.error('Counts must be positive and client levels at most 256')
    if args.model_seconds < 0 or args.timeout <= 0:
        parser.error('Model delay must be non-negative and timeout positive')
    if args.pg_pool_size < 0:
        parser.error('Pool size must be non-negative')
    dsn = os.environ.get('CTHULHU_TEST_DATABASE_URL')
    if not dsn:
        parser.error('Set CTHULHU_TEST_DATABASE_URL to a disposable database')
    args.output.mkdir(parents=True, exist_ok=False)
    schema = 'cthulhu_load_' + uuid4().hex
    store = PostgresStore(dsn, schema)
    store.initialize()
    context = multiprocessing.get_context('spawn')
    ready, generations = context.Queue(), context.Value('i', 0)
    workers, monitor_stop, resources = [], threading.Event(), {'peak_worker_rss_mb': 0, 'worker_cpu_seconds': 0}
    report = {'timestamp': datetime.now(timezone.utc).isoformat(), 'profile': args.profile,
              'model': 'live' if args.live_model else 'simulated', 'model_seconds': args.model_seconds,
              'workers': args.workers, 'threads': args.threads, 'turns_per_client': args.turns,
              'request_timing': args.request_timing,
              'pg_pool_size': args.pg_pool_size,
              'platform': platform.platform(), 'python': platform.python_version(),
              'logical_cpus': psutil.cpu_count(), 'machine_ram_gb': round(psutil.virtual_memory().total / 2**30, 2),
              'stages': [], 'resources': resources}
    try:
        with tempfile.TemporaryDirectory(prefix='cthulhu-load-') as temporary:
            secret = secrets.token_hex(32)
            for index in range(args.workers):
                config = dict(dsn=dsn, schema=schema, secret=secret, threads=args.threads,
                              model_seconds=args.model_seconds, live_model=args.live_model,
                              profile=args.profile, data_dir=str(Path(temporary) / str(index)),
                              request_timing=args.request_timing,
                              pg_pool_size=args.pg_pool_size,
                              timing_file=str((args.output / f'timings-{index}.jsonl').resolve()))
                process = context.Process(target=_serve, args=(config, ready, generations))
                process.start()
                workers.append(process)
            addresses = [ready.get(timeout=30) for _ in workers]
            urls = [f'http://127.0.0.1:{port}' for _, port in addresses]
            processes = [psutil.Process(pid) for pid, _ in addresses]
            baseline_cpu = sum(p.cpu_times().user + p.cpu_times().system for p in processes)

            def monitor():
                while not monitor_stop.wait(0.25):
                    try:
                        rss = sum(p.memory_info().rss for p in processes) / 2**20
                        resources['peak_worker_rss_mb'] = round(max(resources['peak_worker_rss_mb'], rss), 2)
                    except psutil.Error:
                        return
            sampler = threading.Thread(target=monitor, daemon=True)
            sampler.start()
            try:
                consumed = {}
                for users in levels:
                    stage = run_stage(urls, users, args.turns, args.timeout, args.request_timing)
                    if args.request_timing:
                        records = []
                        for path in args.output.glob('timings-*.jsonl'):
                            with path.open(encoding='utf-8') as timing_file:
                                timing_file.seek(consumed.get(path, 0))
                                while True:
                                    position = timing_file.tell()
                                    line = timing_file.readline()
                                    if not line.endswith('\n'):
                                        timing_file.seek(position)
                                        break
                                    record = json.loads(line)
                                    if record['route'] == '/api/game/action/stream':
                                        records.append(record)
                                consumed[path] = timing_file.tell()
                        stage['server_timing'] = summarize_timings(records, stage['client_samples'])
                    report['stages'].append(stage)
                    print(json.dumps({key: value for key, value in stage.items()
                                      if key != 'client_samples'}), flush=True)
                resources['worker_cpu_seconds'] = round(
                    sum(p.cpu_times().user + p.cpu_times().system for p in processes) - baseline_cpu, 3)
                snapshots = store.snapshots()
                receipts = [receipt for payload, _ in snapshots
                            for receipt in (payload.get('app_state') or {}).get('actions', {}).values()]
                report['audit'] = {'games': len(snapshots), 'receipt_statuses': dict(Counter(r['status'] for r in receipts)),
                                   'simulated_llm_calls': generations.value if not args.live_model else None}
            finally:
                monitor_stop.set()
                sampler.join(2)
                for process in workers:
                    if process.is_alive():
                        process.terminate()
                    process.join(5)
    finally:
        for process in workers:
            if process.is_alive():
                process.terminate()
                process.join(5)
        ready.close()
        assert schema.startswith('cthulhu_load_') and len(schema) == 45
        with store.connect() as connection:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
    (args.output / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (args.output / 'report.md').write_text(markdown_report(report), encoding='utf-8')
    allowed = {'ok', 'http_429'} if args.profile == 'guardrails' else {'ok'}
    failed = any(stage['verification_errors'] or any(k not in allowed for k in stage['outcomes'])
                 or any(k not in allowed for k in stage['setup_outcomes']) for stage in report['stages'])
    print('Report:', args.output / 'report.md', flush=True)
    return int(failed)


def summarize_timings(records, samples=()):
    names = ['postgres.connect', 'postgres.pool_wait', 'postgres.session_lock', 'postgres.read',
             'postgres.write', 'postgres.rate_limit', 'session.local_lock',
             'llm.chat', 'llm.tools', 'llm.endpoint_selection']
    durations = {'wsgi': [record['seconds'] for record in records]}
    durations.update({name: [r['spans'].get(name, {}).get('seconds', 0) for r in records]
                      for name in names})
    indexed = {r['request_id']: r for r in records}
    # Same-machine monotonic durations, paired by server-generated ID. This
    # residual includes client/network/server-queue time; it is not queue-only.
    durations['outside_wsgi'] = [s['seconds'] - indexed[s['request_id']]['seconds']
                                 for s in samples if s.get('request_id') in indexed]
    return {'records': len(records),
            'paired_records': len(durations['outside_wsgi']),
            'seconds': {name: {f'p{p}': percentile(values, p) for p in (50, 95, 99)}
                        for name, values in durations.items()}}


if __name__ == '__main__':
    raise SystemExit(main())
