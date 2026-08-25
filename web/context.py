#!/usr/bin/env python3
"""
Per-application state and the decorators the routes share.

This was the closure of create_app. It is a class now so the blueprint modules
can reach it without importing app.py (which would be a cycle) and without a
module-level singleton (which would leak sessions between apps in one process —
the tests build several).

The factory constructs one and stores it on ``app.extensions["cthulhu"]``;
routes reach it through :func:`ctx`, which resolves against ``current_app``.
"""

import logging
import os
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Optional
from uuid import uuid4

from flask import current_app, jsonify, request, session

from core.game_generative import GenerativeGameEngine
from core.generative_save import GenerativeSave

logger = logging.getLogger(__name__)

EXTENSION_KEY = "cthulhu"


@dataclass
class GameSession:
    """Holds one player's game plus the lock that serializes access to it."""
    sid: str
    engine: Optional[GenerativeGameEngine] = None
    investigator: Optional[object] = None
    pending_roll: Optional[dict] = None
    lock: threading.Lock = field(default_factory=threading.Lock)
    last_access: float = field(default_factory=time.time)


class GameContext:
    """Everything the routes need that is not the request itself."""

    RATE_LIMITS = {
        "action": (20, 60),    # 20 turns/min per IP — humans type slower
        "start": (6, 60),      # new games / loads
        "feedback": (6, 60),
    }

    def __init__(self, config: dict):
        self.config = config or {}
        cfg = self.config

        self.data_dir = Path(cfg.get('DATA_DIR',
                                     os.environ.get('DATA_DIR',
                                                    str(Path(__file__).parent.parent))))
        # Generated location images. SDXL scene generation is gated behind a
        # flag (off by default) — the procedural art was more confusing than
        # helpful, so the game runs text-only unless ENABLE_IMAGES=1.
        self.images_dir = Path(cfg.get('GENERATED_IMAGES_DIR',
                                       str(self.data_dir / 'game' / 'generated')))
        self.images_enabled = cfg.get('IMAGES_ENABLED',
                                      os.environ.get('ENABLE_IMAGES', '0') == '1')
        # Idle sessions are evicted (and their engines closed) after this long.
        self.session_ttl = int(cfg.get('SESSION_TTL',
                                       os.environ.get('SESSION_TTL', '3600')))
        # Reject oversized actions before they reach the model (cost/DoS guard).
        # The engine separately sanitizes + truncates; this is the outer bound.
        self.max_action_len = int(cfg.get('MAX_ACTION_LEN',
                                          os.environ.get('MAX_ACTION_LEN', '2000')))
        self.admin_token = cfg.get('ADMIN_TOKEN', os.environ.get("ADMIN_TOKEN", ""))
        self.exclude_names = {
            n.strip().lower()
            for n in (cfg.get('EXCLUDE_NAMES',
                              os.environ.get("EXCLUDE_NAMES", ""))).split(",")
            if n.strip()
        }

        self._sessions: dict[str, GameSession] = {}
        self._registry_lock = threading.Lock()
        self._rl_lock = threading.Lock()
        self._rl_hits: dict = {}
        # Image generation runs in a background thread: SDXL inference takes
        # 30s+ and must not block request handlers (which hold the session lock).
        self._generating_locations: set = set()
        self._generating_lock = threading.Lock()

    # -- configuration ------------------------------------------------------

    def load_secret_key(self) -> str:
        """Resolve a Flask signing key that is STABLE across restarts."""
        key = self.config.get('SECRET_KEY') or os.environ.get('SECRET_KEY')
        if key:
            return key
        # In production set SECRET_KEY; the file fallback lives under DATA_DIR
        # so it survives restarts when a volume is mounted there.
        secret_file = self.data_dir / '.flask_secret'
        if secret_file.exists():
            return secret_file.read_text(encoding='utf-8').strip()
        key = secrets.token_hex(32)
        try:
            secret_file.parent.mkdir(parents=True, exist_ok=True)
            secret_file.write_text(key, encoding='utf-8')
            logger.warning("No SECRET_KEY set; generated one in .flask_secret. "
                           "Set SECRET_KEY in the environment for production.")
        except OSError:
            logger.warning("No SECRET_KEY set and .flask_secret is unwritable; "
                           "web sessions will NOT survive a restart.")
        return key

    # -- session registry ---------------------------------------------------

    @property
    def sessions(self) -> dict:
        """Live registry. Read-only for callers; /api/health counts it."""
        return self._sessions

    def _sweep_idle(self) -> None:
        """Drop and clean up sessions idle longer than SESSION_TTL."""
        now = time.time()
        stale = []
        with self._registry_lock:
            for sid, gs in list(self._sessions.items()):
                if now - gs.last_access > self.session_ttl:
                    del self._sessions[sid]
                    stale.append(gs)
        for gs in stale:
            self.cleanup_session(gs)

    def cleanup_session(self, gs: GameSession) -> None:
        """Release a session's engine resources (Neo4j driver, memory)."""
        if gs.engine:
            try:
                gs.engine.close()
            except Exception:
                logger.warning("engine.close() failed for sid=%s", gs.sid, exc_info=True)

    def get_session(self) -> GameSession:
        """Resolve (or create) the GameSession for the current cookie."""
        sid = session.get('sid')
        if not sid:
            sid = uuid4().hex
            session['sid'] = sid
        self._sweep_idle()
        with self._registry_lock:
            gs = self._sessions.get(sid)
            if gs is None:
                gs = GameSession(sid=sid)
                self._sessions[sid] = gs
            gs.last_access = time.time()
            return gs

    def ensure_engine(self, gs: GameSession) -> bool:
        """Lazily reload a session's game from its autosave (e.g. after a restart).

        Returns True if an engine is available afterwards.
        """
        if gs.engine is not None:
            return True
        if GenerativeSave.exists(gs.sid):
            try:
                gs.engine = GenerativeGameEngine.load_game(gs.sid)
                gs.investigator = gs.engine.state.investigator
                app_state = GenerativeSave.load_app_state(gs.sid) or {}
                gs.pending_roll = app_state.get("pending_roll")
                return True
            except Exception:
                logger.warning("resume failed for sid=%s", gs.sid, exc_info=True)
                return False
        return False

    def autosave(self, gs: GameSession) -> None:
        """Persist the session's game + app-layer pending_roll, keyed by cookie sid."""
        if not gs.engine:
            return
        try:
            gs.engine.save_game(app_state={"pending_roll": gs.pending_roll})
        except Exception:
            logger.warning("autosave failed for sid=%s", gs.sid, exc_info=True)

    # -- rate limiting ------------------------------------------------------

    def client_ip(self) -> str:
        return (request.headers.get("CF-Connecting-IP")
                or (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
                or request.remote_addr or "?")

    def allow(self, bucket: str) -> bool:
        """Sliding-window check for this IP. False means over budget."""
        limit, window = self.RATE_LIMITS[bucket]
        ip = self.client_ip()
        now = time.time()
        with self._rl_lock:
            dq = self._rl_hits.setdefault((bucket, ip), deque())
            while dq and now - dq[0] > window:
                dq.popleft()
            if len(dq) >= limit:
                return False
            dq.append(now)
            return True

    # -- images -------------------------------------------------------------

    def request_image_generation(self, location_state) -> None:
        """Kick off background image generation for a location (idempotent)."""
        key = location_state.key
        with self._generating_lock:
            if key in self._generating_locations:
                return
            self._generating_locations.add(key)

        def work():
            try:
                from game.game_image_integration import generate_for_location
                generate_for_location(location_state)
            except Exception as e:
                print(f"Warning: Could not generate image for {key}: {e}")
            finally:
                with self._generating_lock:
                    self._generating_locations.discard(key)

        threading.Thread(target=work, daemon=True, name=f"imagegen-{key}").start()


def ctx() -> GameContext:
    """The current app's context. Only valid inside an app/request context."""
    return current_app.extensions[EXTENSION_KEY]


def investigator_stats(investigator) -> dict:
    return {
        "HP": investigator.characteristics['HP'],
        "maxHP": investigator.characteristics.get('max_hp',
                                                  investigator.characteristics['HP']),
        "SAN": investigator.characteristics['SAN'],
        "Luck": investigator.characteristics['Luck'],
    }


def synchronized(f):
    """Resolve the caller's GameSession and serialize the handler on its lock.

    Distinct sessions run concurrently; a single session stays serialized. The
    resolved GameSession is passed as the handler's first argument.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        gs = ctx().get_session()
        with gs.lock:
            return f(gs, *args, **kwargs)
    return wrapper


def rate_limited(bucket):
    """Reject with 429 when an IP exceeds the bucket's sliding-window limit."""
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not ctx().allow(bucket):
                return jsonify({"error": "Too many requests — slow down"}), 429
            return f(*args, **kwargs)
        return wrapper
    return deco
