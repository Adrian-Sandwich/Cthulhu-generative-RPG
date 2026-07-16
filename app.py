#!/usr/bin/env python3
"""
Cthulhu Lighthouse Game - Web Interface
Flask backend for the generative RPG
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session, Response
from flask_cors import CORS
import json
import logging
import os
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Optional
from uuid import uuid4
from core.game_generative import GenerativeGameEngine
from core.generative_save import GenerativeSave
from core.archetypes import get_archetype_sheets, create_investigator
from core.moderation import is_allowed
# NOTE: game.game_image_integration pulls in torch/diffusers; it is imported
# lazily inside request_image_generation so the default (image-less) deploy
# doesn't need those heavy, GPU-oriented dependencies.

logger = logging.getLogger(__name__)

app = Flask(__name__)


def _load_secret_key() -> str:
    """
    Resolve a Flask signing key that is STABLE across restarts.

    A regenerated key invalidates existing cookies, which would orphan every
    player's session id and break web resume. Prefer the SECRET_KEY env var;
    otherwise persist a generated key to a gitignored .flask_secret file.
    """
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    # In production set SECRET_KEY; the file fallback lives under DATA_DIR so it
    # survives restarts when a volume is mounted there.
    secret_file = Path(os.environ.get('DATA_DIR', str(Path(__file__).parent))) / '.flask_secret'
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


app.config['SECRET_KEY'] = _load_secret_key()
# Cookie hardening: Lax blocks cross-site POST CSRF (e.g. a forged /reset that
# would wipe a player's autosave) while still allowing normal top-level nav.
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Frontend is served by this same app; CORS only needed for external
# origins, configurable via comma-separated CORS_ORIGINS env var. When CORS is
# enabled we must allow credentials so the session cookie rides cross-origin.
_cors_origins = [o for o in os.environ.get('CORS_ORIGINS', '').split(',') if o]
if _cors_origins:
    CORS(app, origins=_cors_origins, supports_credentials=True)

# Generated location images. SDXL scene generation is gated behind a
# flag (off by default) — the procedural art was more confusing than
# helpful, so the game runs text-only unless ENABLE_IMAGES=1.
GENERATED_IMAGES_DIR = Path(__file__).parent / 'game' / 'generated'
IMAGES_ENABLED = os.environ.get('ENABLE_IMAGES', '0') == '1'

# Idle sessions are evicted (and their engines closed) after this long.
SESSION_TTL = int(os.environ.get('SESSION_TTL', '3600'))

# Reject oversized actions before they reach the model (cost/DoS guard). The
# engine separately sanitizes + truncates; this is the outer bound.
MAX_ACTION_LEN = 2000


@app.route('/images/<path:filename>')
def serve_generated_image(filename):
    """Serve generated location images"""
    return send_from_directory(GENERATED_IMAGES_DIR, filename)


# ---------------------------------------------------------------------------
# Per-session game registry
#
# Each browser gets its own GameSession keyed by a signed-cookie session id, so
# concurrent players never share or corrupt each other's game. A single player
# (one cookie) gets exactly one entry, so single-user behavior is unchanged.
# ---------------------------------------------------------------------------

@dataclass
class GameSession:
    """Holds one player's game plus the lock that serializes access to it."""
    sid: str
    engine: Optional[GenerativeGameEngine] = None
    investigator: Optional[object] = None
    pending_roll: Optional[dict] = None
    lock: threading.Lock = field(default_factory=threading.Lock)
    last_access: float = field(default_factory=time.time)


_sessions: dict[str, GameSession] = {}
_registry_lock = threading.Lock()


def _sweep_idle():
    """Drop and clean up sessions idle longer than SESSION_TTL."""
    now = time.time()
    stale = []
    with _registry_lock:
        for sid, gs in list(_sessions.items()):
            if now - gs.last_access > SESSION_TTL:
                del _sessions[sid]
                stale.append(gs)
    for gs in stale:
        _cleanup_session(gs)


def _cleanup_session(gs: GameSession):
    """Release a session's engine resources (Neo4j driver, memory)."""
    if gs.engine:
        try:
            gs.engine.close()
        except Exception:
            logger.warning("engine.close() failed for sid=%s", gs.sid, exc_info=True)


def _get_session() -> GameSession:
    """Resolve (or create) the GameSession for the current cookie."""
    sid = session.get('sid')
    if not sid:
        sid = uuid4().hex
        session['sid'] = sid
    _sweep_idle()
    with _registry_lock:
        gs = _sessions.get(sid)
        if gs is None:
            gs = GameSession(sid=sid)
            _sessions[sid] = gs
        gs.last_access = time.time()
        return gs


# ---------------------------------------------------------------------------
# Lightweight per-IP rate limiting — required before any public exposure
# (tunnel). Sliding window per (bucket, ip); behind Cloudflare the real client
# IP arrives in CF-Connecting-IP.
# ---------------------------------------------------------------------------
_rl_lock = threading.Lock()
_rl_hits = {}
RATE_LIMITS = {
    "action": (20, 60),    # 20 turns/min per IP — humans type slower
    "start": (6, 60),      # new games / loads
    "feedback": (6, 60),
}


def _client_ip() -> str:
    return (request.headers.get("CF-Connecting-IP")
            or (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
            or request.remote_addr or "?")


def rate_limited(bucket):
    """Reject with 429 when an IP exceeds the bucket's sliding-window limit."""
    limit, window = RATE_LIMITS[bucket]

    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = _client_ip()
            now = time.time()
            with _rl_lock:
                dq = _rl_hits.setdefault((bucket, ip), deque())
                while dq and now - dq[0] > window:
                    dq.popleft()
                if len(dq) >= limit:
                    return jsonify({"error": "Too many requests — slow down"}), 429
                dq.append(now)
            return f(*args, **kwargs)
        return wrapper
    return deco


def synchronized(f):
    """Resolve the caller's GameSession and serialize the handler on its lock.

    Distinct sessions run concurrently; a single session stays serialized.
    The resolved GameSession is passed as the handler's first argument.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        gs = _get_session()
        with gs.lock:
            return f(gs, *args, **kwargs)
    return wrapper


def _ensure_engine(gs: GameSession) -> bool:
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


# Image generation runs in a background thread: SDXL inference takes
# 30s+ and must not block request handlers (which hold the session lock).
_generating_locations = set()
_generating_lock = threading.Lock()


def request_image_generation(location_state):
    """Kick off background image generation for a location (idempotent)."""
    key = location_state.key
    with _generating_lock:
        if key in _generating_locations:
            return
        _generating_locations.add(key)

    def work():
        try:
            from game.game_image_integration import generate_for_location
            generate_for_location(location_state)
        except Exception as e:
            print(f"Warning: Could not generate image for {key}: {e}")
        finally:
            with _generating_lock:
                _generating_locations.discard(key)

    threading.Thread(target=work, daemon=True, name=f"imagegen-{key}").start()


def _autosave(gs: GameSession):
    """Persist the session's game + app-layer pending_roll, keyed by cookie sid."""
    if not gs.engine:
        return
    try:
        gs.engine.save_game(app_state={"pending_roll": gs.pending_roll})
    except Exception:
        logger.warning("autosave failed for sid=%s", gs.sid, exc_info=True)


def _investigator_stats(investigator):
    return {
        "HP": investigator.characteristics['HP'],
        "SAN": investigator.characteristics['SAN'],
        "Luck": investigator.characteristics['Luck']
    }


@app.route('/')
def index():
    """Main game interface"""
    return render_template('index.html')


@app.route('/api/archetypes', methods=['GET'])
def get_archetypes():
    """Archetype stat blocks for the character sheet preview"""
    return jsonify({"archetypes": get_archetype_sheets()})


@app.route('/api/game/start', methods=['POST'])
@rate_limited('start')
@synchronized
def start_game(gs):
    """Start a new game"""
    data = request.get_json(silent=True) or {}
    investigator_name = data.get('name', 'Unknown Investigator')
    occupation = data.get('archetype', 'scholar')  # Called 'occupation' in game engine
    # Spanish paused again by request — force English regardless of client.
    # Engine i18n + Spanish roll keywords remain; flip this back to
    # data.get('language','en') (validated) to re-enable.
    language = 'en'

    try:
        # Starting a new game discards any prior engine on this session.
        if gs.engine:
            _cleanup_session(gs)
        gs.pending_roll = None

        gs.investigator = create_investigator(investigator_name, occupation)

        # Engine session id == cookie sid, so the autosave file is per-player.
        gs.engine = GenerativeGameEngine(use_memory=False, session_id=gs.sid, language=language)
        gs.engine.create_game(gs.investigator)

        # Opening narrative so the player knows the situation and that
        # they drive the story with free-text actions (in the chosen language)
        intro = gs.engine.localized_intro()

        _autosave(gs)

        return jsonify({
            "success": True,
            "message": f"Game started! Welcome, {investigator_name}",
            "intro": intro,
            "location": gs.engine.state.location,
            "investigator": {
                "name": gs.investigator.name,
                "archetype": gs.investigator.occupation,
                "HP": gs.investigator.characteristics['HP'],
                "SAN": gs.investigator.characteristics['SAN'],
                "Luck": gs.investigator.characteristics['Luck']
            }
        })
    except Exception as e:
        logger.warning("start_game failed for sid=%s", gs.sid, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/game/saves', methods=['GET'])
@synchronized
def list_saves(gs):
    """List saved games for this session (currently a single autosave per sid)."""
    summary = GenerativeSave.get_session_summary(gs.sid)
    return jsonify({"saves": [summary] if summary else []})


@app.route('/api/game/load', methods=['POST'])
@rate_limited('start')
@synchronized
def load_saved_game(gs):
    """Resume this session's autosaved game from disk."""
    if not GenerativeSave.exists(gs.sid):
        return jsonify({"error": "No saved game for this session"}), 404
    # Drop any in-memory engine first so reload is clean.
    if gs.engine:
        _cleanup_session(gs)
        gs.engine = None
    if not _ensure_engine(gs):
        return jsonify({"error": "Could not load saved game"}), 500
    return jsonify({
        "success": True,
        "turn": gs.engine.state.turn,
        "location": gs.engine.state.location,
        "narrative": gs.engine.state.narrative[-5:] if gs.engine.state.narrative else [],
        "pending_roll": gs.pending_roll,
        "state": _investigator_stats(gs.investigator)
    })


@app.route('/api/game/state', methods=['GET'])
@synchronized
def get_game_state(gs):
    """Get current game state"""
    if not _ensure_engine(gs) or not gs.investigator:
        return jsonify({"error": "Game not started"}), 400

    # Get location state and request image generation if missing
    location_state = None
    if gs.engine.location_state:
        location_state = gs.engine.location_state.get_location(gs.engine.state.location)
    image_url = None
    image_generating = False
    if IMAGES_ENABLED and location_state:
        if not location_state.generated_image_path:
            request_image_generation(location_state)
            image_generating = True
        else:
            image_path = Path(location_state.generated_image_path)
            image_url = f"/images/{image_path.name}"

    inv = gs.investigator
    return jsonify({
        "location": gs.engine.state.location,
        "turn": gs.engine.state.turn,
        "image_url": image_url,
        "image_generating": image_generating,
        "pending_roll": gs.pending_roll,
        "npcs": gs.engine.get_npc_status(),
        "sanity_corruption": gs.engine.sanity_corruption_level(),
        "resources": gs.engine.resources_status(),
        "investigator": {
            "name": inv.name,
            "archetype": inv.occupation,
            "HP": inv.characteristics['HP'],
            "SAN": inv.characteristics['SAN'],
            "Luck": inv.characteristics['Luck'],
            "characteristics": inv.characteristics,
            "skills": inv.skills,
            "inventory": inv.inventory
        },
        "narrative": gs.engine.state.narrative[-5:] if gs.engine.state.narrative else []
    })


@app.route('/api/game/action', methods=['POST'])
@rate_limited('action')
@synchronized
def process_action(gs):
    """Process player action"""
    if not _ensure_engine(gs) or not gs.investigator:
        return jsonify({"error": "Game not started"}), 400

    if gs.pending_roll:
        return jsonify({"error": "Resolve the pending roll first"}), 409

    data = request.get_json(silent=True) or {}
    player_input = data.get('action', '')

    if not isinstance(player_input, str) or not player_input.strip():
        return jsonify({"error": "Action cannot be empty"}), 400
    if len(player_input) > MAX_ACTION_LEN:
        return jsonify({"error": "Action too long"}), 413
    if not is_allowed(player_input):
        return jsonify({"error": "That action can't be processed."}), 422

    try:
        result = gs.engine.process_player_action(player_input)
        if result.get("error"):
            return jsonify({"error": result["error"]}), 400
        return jsonify(_finalize_turn(gs, result))
    except Exception as e:
        logger.warning("process_action failed for sid=%s", gs.sid, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


def _finalize_turn(gs, result):
    """Apply a turn's consequences and build the response payload.

    Shared by the JSON action endpoint and the SSE streaming endpoint. The
    actual consequence logic lives in engine.apply_turn_consequences (also
    used by the terminal loop) so frontends can't drift.
    """
    outcome = gs.engine.apply_turn_consequences(result)
    if outcome["pending_roll"] and not gs.pending_roll:
        gs.pending_roll = outcome["pending_roll"]

    # A reached ending archives the playthrough automatically.
    if gs.engine.state.ending_reached:
        try:
            gs.engine.export_playtest("ending")
        except Exception:
            logger.warning("playtest export on ending failed", exc_info=True)

    _autosave(gs)

    # Guard the DM's output too: if the model produced disallowed content,
    # swap it for a safe in-fiction line rather than showing it.
    narrative = result.get("narrative", "")
    if narrative and not is_allowed(narrative):
        narrative = "The scene blurs; your mind refuses to hold what you just perceived."

    return {
        "success": True,
        "turn": gs.engine.state.turn,
        "location": gs.engine.state.location,
        "narrative": narrative,
        "events": outcome["events"],
        "sanity_corruption": result.get("sanity_corruption", 0),
        "sanity_recovered": result.get("sanity_recovered", 0),
        "npcs": result.get("npc_status", []),
        "resources": gs.engine.resources_status(),
        "combat": gs.engine.combat_status(),
        "pending_roll": gs.pending_roll,
        "state": _investigator_stats(gs.investigator)
    }


@app.route('/api/game/action/stream', methods=['POST'])
@rate_limited('action')
def process_action_stream():
    """Stream the DM's narration token-by-token over Server-Sent Events.

    Emits `data:` frames with {chunk} as the model writes, then a final
    `event: done` frame carrying the same payload as /api/game/action.
    """
    gs = _get_session()
    data = request.get_json(silent=True) or {}
    player_input = data.get('action', '')
    if not isinstance(player_input, str) or not player_input.strip():
        return jsonify({"error": "Action cannot be empty"}), 400
    if len(player_input) > MAX_ACTION_LEN:
        return jsonify({"error": "Action too long"}), 413
    if not is_allowed(player_input):
        return jsonify({"error": "That action can't be processed."}), 422

    def stream():
        import json as _json
        import queue as _queue
        import threading as _threading

        with gs.lock:
            if not _ensure_engine(gs) or not gs.investigator:
                yield f"event: error\ndata: {_json.dumps({'error': 'Game not started'})}\n\n"
                return
            if gs.pending_roll:
                yield f"event: error\ndata: {_json.dumps({'error': 'Resolve the pending roll first'})}\n\n"
                return

            q = _queue.Queue()
            holder = {}

            # Suppress mechanic tags ([ROLL: ...], [SANITY_CHECK: ...]) from the
            # live stream — otherwise the player watches raw tags appear and
            # then vanish when the cleaned final text replaces the stream.
            tag_buf = {"pending": ""}

            def on_chunk(text):
                data = tag_buf["pending"] + text
                tag_buf["pending"] = ""
                out = []
                while data:
                    if data.startswith("["):
                        close = data.find("]")
                        if close == -1:
                            if len(data) > 120:   # unterminated — not a tag
                                out.append(data)
                                data = ""
                            else:
                                tag_buf["pending"] = data
                                data = ""
                        else:
                            data = data[close + 1:]  # drop the whole [tag]
                    else:
                        nxt = data.find("[")
                        if nxt == -1:
                            out.append(data)
                            data = ""
                        else:
                            out.append(data[:nxt])
                            data = data[nxt:]
                clean = "".join(out)
                if clean:
                    q.put(clean)

            def worker():
                try:
                    holder['res'] = gs.engine.process_player_action(player_input, on_chunk=on_chunk)
                except Exception as exc:
                    holder['err'] = str(exc)
                    logger.warning("stream turn failed for sid=%s", gs.sid, exc_info=True)
                finally:
                    q.put(None)  # sentinel: generation finished

            worker_thread = _threading.Thread(target=worker, daemon=True)
            worker_thread.start()

            while True:
                chunk = q.get()
                if chunk is None:
                    break
                yield f"data: {_json.dumps({'chunk': chunk})}\n\n"
            worker_thread.join()

            if 'err' in holder:
                yield f"event: error\ndata: {_json.dumps({'error': holder['err']})}\n\n"
                return

            res = holder.get('res', {})
            if res.get("error"):
                yield f"event: error\ndata: {_json.dumps({'error': res['error']})}\n\n"
                return

            final = _finalize_turn(gs, res)
            yield f"event: done\ndata: {_json.dumps(final)}\n\n"

    return Response(stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/game/roll', methods=['POST'])
@rate_limited('action')
@synchronized
def execute_roll(gs):
    """Player throws the die for the pending skill check"""
    if not _ensure_engine(gs) or not gs.investigator:
        return jsonify({"error": "Game not started"}), 400

    if not gs.pending_roll:
        return jsonify({"error": "No pending roll"}), 400

    try:
        roll = gs.pending_roll
        gs.pending_roll = None

        # Server rolls the actual die (the client animation is theater)
        result = gs.engine.execute_skill_check(roll["skill"], roll["difficulty"])

        narrative = ""
        consequence = None
        if roll.get("combat"):
            # Combat round: resolve mechanically (your attack + enemy counter).
            combat_res = gs.engine.resolve_combat_round(
                result["success"], critical=result.get("critical"))
            narrative = combat_res.get("narrative", "")
            if not combat_res.get("combat_over") and gs.engine.state.active_combat:
                # Fight continues — queue the next attack throw.
                gs.pending_roll = gs.engine.combat_attack_roll()
        else:
            # Non-combat skill check: the DM narrates the consequence.
            outcome = gs.engine.resolve_roll_consequences()
            if isinstance(outcome, dict):
                narrative = outcome.get("narrative", "")
                consequence = outcome.get("consequence")

        _autosave(gs)

        return jsonify({
            "success": True,
            "skill": roll["skill"],
            "difficulty": roll["difficulty"],
            "roll": result["roll"],
            "target": result["target"],
            "roll_success": result["success"],
            "message": result["message"],
            "narrative": narrative,
            "consequence": consequence,  # mechanical bite on failure (kind/amount/label/fumble)
            "empty": result.get("empty", False),
            "resources": gs.engine.resources_status(),
            "combat": gs.engine.combat_status(),
            "pending_roll": gs.pending_roll,
            "turn": gs.engine.state.turn,
            "location": gs.engine.state.location,
            "state": _investigator_stats(gs.investigator)
        })
    except Exception as e:
        logger.warning("execute_roll failed for sid=%s", gs.sid, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/game/flee', methods=['POST'])
@synchronized
def flee_combat(gs):
    """Break off the current fight (the enemy gets one free attack)."""
    if not _ensure_engine(gs) or not gs.investigator:
        return jsonify({"error": "Game not started"}), 400
    if not gs.engine.state.active_combat:
        return jsonify({"error": "Not in combat"}), 400
    try:
        res = gs.engine.attempt_flee()
        gs.pending_roll = None
        _autosave(gs)
        return jsonify({
            "success": True,
            "narrative": res.get("narrative", ""),
            "combat": gs.engine.combat_status(),
            "pending_roll": None,
            "turn": gs.engine.state.turn,
            "location": gs.engine.state.location,
            "state": _investigator_stats(gs.investigator)
        })
    except Exception as e:
        logger.warning("flee failed for sid=%s", gs.sid, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/game/reset', methods=['POST'])
@synchronized
def reset_game(gs):
    """Reset this session's game to start, releasing its resources."""
    # Archive the run first — every playthrough is data to learn from.
    if gs.engine and gs.engine.state:
        try:
            gs.engine.export_playtest("reset")
        except Exception:
            logger.warning("playtest export on reset failed", exc_info=True)
    _cleanup_session(gs)
    gs.engine = None
    gs.investigator = None
    gs.pending_roll = None
    # Drop the autosave so a stale game isn't lazily resumed.
    try:
        GenerativeSave.delete(gs.sid)
    except Exception:
        logger.warning("save delete failed for sid=%s", gs.sid, exc_info=True)

    return jsonify({"success": True, "message": "Game reset"})


@app.route('/api/feedback', methods=['POST'])
@rate_limited('feedback')
@synchronized
def leave_feedback(gs):
    """Store player feedback, linked to their session for later correlation
    with the autosave/playtest archive."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Feedback cannot be empty"}), 400
    if len(text) > 2000:
        return jsonify({"error": "Feedback too long"}), 413
    rating = data.get('rating')
    rating = int(rating) if isinstance(rating, (int, float)) and 1 <= rating <= 5 else None

    entry = {
        "at": datetime.now().isoformat(),
        "sid": gs.sid,
        "text": text.strip(),
        "rating": rating,
        "turn": gs.engine.state.turn if gs.engine and gs.engine.state else None,
        "investigator": gs.investigator.name if gs.investigator else None,
        "location": gs.engine.state.location if gs.engine and gs.engine.state else None,
    }
    try:
        fb_dir = Path(os.environ.get("DATA_DIR", ".")) / "feedback"
        fb_dir.mkdir(parents=True, exist_ok=True)
        with open(fb_dir / "feedback.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.warning("feedback write failed", exc_info=True)
        return jsonify({"error": "Could not save feedback"}), 500
    return jsonify({"success": True, "message": "Thank you, investigator."})


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "sessions": len(_sessions)})


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', '5000'))
    # Default: loopback only (no one else can reach the game). Set HOST=0.0.0.0
    # to open it to the LAN — anyone on your network can then play at
    # http://<your-lan-ip>:<port>. Sessions are already isolated per browser.
    host = os.environ.get('HOST', '127.0.0.1')
    # Never run the Werkzeug debugger (RCE) on a non-loopback bind — a public
    # tunnel behind HOST=0.0.0.0 would otherwise expose it.
    if debug and host != '127.0.0.1':
        logger.warning("Refusing FLASK_DEBUG=1 with non-loopback HOST — forcing debug off.")
        debug = False
    app.run(debug=debug, host=host, port=port)
