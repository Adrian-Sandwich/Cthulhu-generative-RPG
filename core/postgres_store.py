"""Shared snapshots and session coordination for PostgreSQL deployments.

A session advisory lock lives on one connection for the entire operation.
Every write uses that same connection: losing it prevents a stale worker from
reconnecting and overwriting a newer turn. Autocommit keeps LLM generation
outside transactions. Use a direct connection or session-mode pooler.
"""

from contextlib import contextmanager
import hashlib
import atexit
import os
import threading
from pathlib import Path
from core.timing import measure, timed

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool


class StorageUnavailable(OSError):
    pass


def lock_key(value):
    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], 'big', signed=True)


class PostgresStore:
    def __init__(self, dsn, schema='cthulhu', pool_size=0, pool_timeout=2.0):
        self.dsn = dsn
        self.schema = schema
        self.table = sql.Identifier(schema, 'game_saves')
        if pool_size < 0 or not 0 < pool_timeout <= 60:
            raise ValueError('Invalid PostgreSQL pool limits')
        self.pool_size, self.pool_timeout = pool_size, pool_timeout
        self._pool = None
        self._pool_lock = threading.Lock()
        self._pool_pid = None

    def close(self):
        if self._pool is not None:
            self._pool.close()

    @contextmanager
    def short_connection(self):
        """Only stateless operations; session advisory locks never enter here."""
        if not self.pool_size:
            with self.connect() as connection:
                yield connection
            return
        with self._pool_lock:
            if self._pool is None:
                self._pool = ConnectionPool(
                    self.dsn, min_size=0, max_size=self.pool_size,
                    timeout=self.pool_timeout, max_waiting=64, open=True,
                    kwargs={'autocommit': True, 'connect_timeout': 5,
                            'options': '-c statement_timeout=15000'},
                    check=ConnectionPool.check_connection)
                self._pool_pid = os.getpid()
                atexit.register(self.close)
            if self._pool_pid != os.getpid():
                raise StorageUnavailable('Database pool must be opened after worker fork')
            pool = self._pool
        try:
            with measure('postgres.pool_wait'):
                connection = pool.getconn()
            try:
                yield connection
            finally:
                pool.putconn(connection)
        except psycopg.Error:
            raise StorageUnavailable('Game storage is temporarily unavailable') from None

    @contextmanager
    def connect(self):
        try:
            with measure('postgres.connect'):
                connection = psycopg.connect(self.dsn, autocommit=True, connect_timeout=5,
                                             options='-c statement_timeout=15000')
            with connection:
                yield connection
        except psycopg.Error:
            # Do not expose DSNs, database names or credentials to browsers.
            raise StorageUnavailable('Game storage is temporarily unavailable') from None

    def initialize(self):
        """Explicit, idempotent schema setup; never performed by web workers."""
        migration = Path(__file__).parent.parent / 'migrations' / '001_postgres.sql'
        with self.connect() as connection:
            with connection.transaction():
                connection.execute('SELECT pg_advisory_xact_lock(%s)',
                                   (lock_key(self.schema + ':migration'),))
                connection.execute(sql.SQL(migration.read_text(encoding='utf-8')).format(
                    schema=sql.Identifier(self.schema)))

    @contextmanager
    def locked(self, sid, blocking=True):
        with self.connect() as connection:
            key = lock_key(self.schema + ':game:' + sid)
            with measure('postgres.session_lock'):
                if blocking:
                    connection.execute('SELECT pg_advisory_lock(%s)', (key,))
                    acquired = True
                else:
                    acquired = connection.execute('SELECT pg_try_advisory_lock(%s)', (key,)).fetchone()[0]
            # Closing the dedicated connection releases the lock, even on an
            # exception. It is never returned to a transaction-mode pool.
            yield LockedSessionStore(self, connection, sid) if acquired else None

    def read(self, sid):
        with self.short_connection() as connection:
            return self._read(connection, sid)

    @timed('postgres.read')
    def _read(self, connection, sid):
        row = connection.execute(sql.SQL('SELECT payload FROM {} WHERE sid = %s').format(
            self.table), (sid,)).fetchone()
        if row is None:
            raise FileNotFoundError('No saved game for this session')
        return row[0]

    def exists(self, sid):
        try:
            self.read(sid)
            return True
        except FileNotFoundError:
            return False

    def ready(self):
        with self.short_connection() as connection:
            connection.execute(sql.SQL('SELECT sid FROM {} LIMIT 0').format(self.table))

    def snapshots(self):
        with self.short_connection() as connection:
            return connection.execute(sql.SQL(
                'SELECT payload, extract(epoch from updated_at) FROM {} ORDER BY updated_at DESC'
            ).format(self.table)).fetchall()

    @timed('postgres.rate_limit')
    def allow(self, bucket, identity, limit, window):
        """One sliding-window budget shared by all workers and servers."""
        table = sql.Identifier(self.schema, 'rate_limits')
        with self.short_connection() as connection, connection.transaction():
            connection.execute('SELECT pg_advisory_xact_lock(%s)',
                               (lock_key(self.schema + ':rate:' + bucket + ':' + identity),))
            connection.execute(sql.SQL('DELETE FROM {} WHERE expires_at < clock_timestamp()').format(table))
            count = connection.execute(sql.SQL(
                'SELECT count(*) FROM {} WHERE bucket=%s AND identity=%s'
            ).format(table), (bucket, identity)).fetchone()[0]
            if count >= limit:
                return False
            connection.execute(sql.SQL(
                "INSERT INTO {} (bucket, identity, expires_at) VALUES (%s, %s, clock_timestamp() + %s * interval '1 second')"
            ).format(table), (bucket, identity, window))
            return True

    def add_feedback(self, entry):
        with self.short_connection() as connection:
            connection.execute(sql.SQL('INSERT INTO {} (payload) VALUES (%s)').format(
                sql.Identifier(self.schema, 'feedback')), (Jsonb(entry),))

    def feedback(self):
        with self.short_connection() as connection:
            return [row[0] for row in connection.execute(sql.SQL(
                'SELECT payload FROM {} ORDER BY id'
            ).format(sql.Identifier(self.schema, 'feedback')))]


class LockedSessionStore:
    """Restricted to one session and its still-live lock connection."""
    def __init__(self, store, connection, sid):
        self.store, self.connection, self.sid = store, connection, sid

    def _check(self, sid):
        if sid != self.sid:
            raise ValueError('Session lock does not own this save')

    def read(self, sid):
        self._check(sid)
        try:
            return self.store._read(self.connection, sid)
        except psycopg.Error:
            raise StorageUnavailable('Game storage connection was lost') from None

    def exists(self, sid):
        try:
            self.read(sid)
            return True
        except FileNotFoundError:
            return False

    @timed('postgres.write')
    def write(self, sid, payload):
        self._check(sid)
        try:
            self.connection.execute(sql.SQL('''
                INSERT INTO {} AS saves (sid, payload) VALUES (%s, %s)
                ON CONFLICT (sid) DO UPDATE SET payload=EXCLUDED.payload,
                    revision=saves.revision+1, updated_at=clock_timestamp()
            ''').format(self.store.table), (sid, Jsonb(payload)))
        except psycopg.Error:
            raise StorageUnavailable('Could not commit the saved game') from None
        return 'postgres:' + sid

    def delete(self, sid):
        self._check(sid)
        try:
            self.connection.execute(sql.SQL('DELETE FROM {} WHERE sid=%s').format(
                self.store.table), (sid,))
        except psycopg.Error:
            raise StorageUnavailable('Could not delete the saved game') from None
