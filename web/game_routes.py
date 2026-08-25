#!/usr/bin/env python3
"""
Routes that need a player session and its engine.

Nine routes, all of them behind @synchronized: distinct players run
concurrently, a single player's turns stay serialized on their own lock.
"""

import json as _json
import logging
import queue as _queue
import threading as _threading
from pathlib import Path

from flask import Blueprint, Response, jsonify, request

from core.archetypes import create_investigator
from core.generative_save import GenerativeSave
from core.game_generative import GenerativeGameEngine
from core.moderation import is_allowed
from web.context import ctx, investigator_stats, rate_limited, synchronized

logger = logging.getLogger(__name__)

bp = Blueprint("game", __name__)


@bp.route('/api/game/start', methods=['POST'])
@rate_limited('start')
@synchronized
def start_game(gs):
    """Start a new game"""
    data = request.get_json(silent=True) or {}
    investigator_name = data.get('name', 'Unknown Investigator')
    occupation = data.get('archetype', 'scholar')
    # Spanish paused again by request — force English regardless of client.
    language = 'en'

    try:
        if gs.engine:
            ctx().cleanup_session(gs)
        gs.pending_roll = None

        gs.investigator = create_investigator(investigator_name, occupation)

        gs.engine = GenerativeGameEngine(use_memory=False, session_id=gs.sid,
                                         language=language)
        gs.engine.create_game(gs.investigator)

        intro = gs.engine.localized_intro()

        ctx().autosave(gs)

        return jsonify({
            "success": True,
            "message": f"Game started! Welcome, {investigator_name}",
            "intro": intro,
            "location": gs.engine.state.location,
            "investigator": {
                "name": gs.investigator.name,
                "archetype": gs.investigator.occupation,
                "HP": gs.investigator.characteristics['HP'],
                "maxHP": gs.investigator.characteristics.get(
                    'max_hp', gs.investigator.characteristics['HP']),
                "SAN": gs.investigator.characteristics['SAN'],
                "Luck": gs.investigator.characteristics['Luck']
            }
        })
    except Exception as e:
        logger.warning("start_game failed for sid=%s", gs.sid, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/game/saves', methods=['GET'])
@synchronized
def list_saves(gs):
    """List saved games for this session (currently a single autosave per sid)."""
    summary = GenerativeSave.get_session_summary(gs.sid)
    return jsonify({"saves": [summary] if summary else []})


@bp.route('/api/game/load', methods=['POST'])
@rate_limited('start')
@synchronized
def load_saved_game(gs):
    """Resume this session's autosaved game from disk."""
    if not GenerativeSave.exists(gs.sid):
        return jsonify({"error": "No saved game for this session"}), 404
    if gs.engine:
        ctx().cleanup_session(gs)
        gs.engine = None
    if not ctx().ensure_engine(gs):
        return jsonify({"error": "Could not load saved game"}), 500
    return jsonify({
        "success": True,
        "turn": gs.engine.state.turn,
        "location": gs.engine.state.location,
        "narrative": gs.engine.state.narrative[-5:] if gs.engine.state.narrative else [],
        "pending_roll": gs.pending_roll,
        "state": investigator_stats(gs.investigator)
    })


@bp.route('/api/game/state', methods=['GET'])
@synchronized
def get_game_state(gs):
    """Get current game state"""
    if not ctx().ensure_engine(gs) or not gs.investigator:
        return jsonify({"error": "Game not started"}), 400

    location_state = None
    if gs.engine.location_state:
        location_state = gs.engine.location_state.get_location(gs.engine.state.location)
    image_url = None
    image_generating = False
    if ctx().images_enabled and location_state:
        if not location_state.generated_image_path:
            ctx().request_image_generation(location_state)
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
        # The client renders the combat HUD from here on every refresh.
        # Omitting it meant renderCombat(undefined) hid the bar and cut the
        # combat music one tick after the turn showed them.
        "combat": gs.engine.combat_status(),
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


@bp.route('/api/game/action', methods=['POST'])
@rate_limited('action')
@synchronized
def process_action(gs):
    """Process player action"""
    if not ctx().ensure_engine(gs) or not gs.investigator:
        return jsonify({"error": "Game not started"}), 400

    if gs.pending_roll:
        return jsonify({"error": "Resolve the pending roll first"}), 409

    data = request.get_json(silent=True) or {}
    player_input = data.get('action', '')

    if not isinstance(player_input, str) or not player_input.strip():
        return jsonify({"error": "Action cannot be empty"}), 400
    if len(player_input) > ctx().max_action_len:
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


def _finalize_turn(gs, result, game=None):
    """Apply a turn's consequences and build the response payload."""
    outcome = gs.engine.apply_turn_consequences(result)
    if outcome["pending_roll"] and not gs.pending_roll:
        gs.pending_roll = outcome["pending_roll"]

    if gs.engine.state.ending_reached:
        try:
            gs.engine.export_playtest("ending")
        except Exception:
            logger.warning("playtest export on ending failed", exc_info=True)

    (game or ctx()).autosave(gs)

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
        "ending": gs.engine.ending_status(),
        "pending_roll": gs.pending_roll,
        "state": investigator_stats(gs.investigator)
    }


@bp.route('/api/game/action/stream', methods=['POST'])
@rate_limited('action')
def process_action_stream():
    """Stream the DM's narration token-by-token over Server-Sent Events."""
    gs = ctx().get_session()
    data = request.get_json(silent=True) or {}
    player_input = data.get('action', '')
    if not isinstance(player_input, str) or not player_input.strip():
        return jsonify({"error": "Action cannot be empty"}), 400
    if len(player_input) > ctx().max_action_len:
        return jsonify({"error": "Action too long"}), 413
    if not is_allowed(player_input):
        return jsonify({"error": "That action can't be processed."}), 422

    # Bind the context here, in request scope. The generator below runs after
    # Flask has torn the request context down, so anything resolved through
    # current_app inside it raises "Working outside of request context" — the
    # same failure mode that made this endpoint 500 on every real turn when it
    # reached for request.is_disconnected.
    game = ctx()

    def stream():
        import json as _json
        import queue as _queue
        import threading as _threading

        with gs.lock:
            if not game.ensure_engine(gs) or not gs.investigator:
                yield f"event: error\ndata: {_json.dumps({'error': 'Game not started'})}\n\n"
                return
            if gs.pending_roll:
                yield f"event: error\ndata: {_json.dumps({'error': 'Resolve the pending roll first'})}\n\n"
                return

            q = _queue.Queue(maxsize=64)
            holder = {}
            cancel_event = _threading.Event()

            tag_buf = {"pending": ""}

            def on_chunk(text):
                if cancel_event.is_set():
                    return
                data = tag_buf["pending"] + text
                tag_buf["pending"] = ""
                out = []
                while data:
                    if data.startswith("["):
                        close = data.find("]")
                        if close == -1:
                            if len(data) > 120:
                                out.append(data)
                                data = ""
                            else:
                                tag_buf["pending"] = data
                                data = ""
                        else:
                            data = data[close + 1:]
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
                    try:
                        q.put(clean, timeout=1.0)
                    except _queue.Full:
                        cancel_event.set()

            def worker():
                try:
                    holder['res'] = gs.engine.process_player_action(player_input, on_chunk=on_chunk)
                except Exception as exc:
                    holder['err'] = str(exc)
                    logger.warning("stream turn failed for sid=%s", gs.sid, exc_info=True)
                finally:
                    try:
                        q.put(None, timeout=1.0)
                    except _queue.Full:
                        pass

            worker_thread = _threading.Thread(target=worker, daemon=True)
            worker_thread.start()

            try:
                while True:
                    try:
                        chunk = q.get(timeout=1.0)
                    except _queue.Empty:
                        # Only cancel_event is readable here: `request` is
                        # unbound once the request context tears down, and
                        # Flask has no `request.is_disconnected` anyway. A
                        # real client disconnect surfaces as an exception on
                        # the next yield, which the finally below cleans up.
                        if cancel_event.is_set():
                            break
                        continue
                    if chunk is None:
                        break
                    yield f"data: {_json.dumps({'chunk': chunk})}\n\n"
            finally:
                cancel_event.set()
                worker_thread.join(timeout=5.0)

            if cancel_event.is_set() and 'res' not in holder:
                return

            if 'err' in holder:
                yield f"event: error\ndata: {_json.dumps({'error': holder['err']})}\n\n"
                return

            res = holder.get('res', {})
            if res.get("error"):
                yield f"event: error\ndata: {_json.dumps({'error': res['error']})}\n\n"
                return

            final = _finalize_turn(gs, res, game)
            yield f"event: done\ndata: {_json.dumps(final)}\n\n"

    return Response(stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@bp.route('/api/game/roll', methods=['POST'])
@rate_limited('action')
@synchronized
def execute_roll(gs):
    """Player throws the die for the pending skill check"""
    if not ctx().ensure_engine(gs) or not gs.investigator:
        return jsonify({"error": "Game not started"}), 400

    if not gs.pending_roll:
        return jsonify({"error": "No pending roll"}), 400

    try:
        roll = gs.pending_roll
        gs.pending_roll = None

        result = gs.engine.execute_skill_check(roll["skill"], roll["difficulty"])

        narrative = ""
        consequence = None
        if roll.get("combat"):
            combat_res = gs.engine.resolve_combat_round(
                result["success"], critical=result.get("critical"))
            narrative = combat_res.get("narrative", "")
            if not combat_res.get("combat_over") and gs.engine.state.active_combat:
                gs.pending_roll = gs.engine.combat_attack_roll()
        else:
            outcome = gs.engine.resolve_roll_consequences()
            if isinstance(outcome, dict):
                narrative = outcome.get("narrative", "")
                consequence = outcome.get("consequence")

        ctx().autosave(gs)

        return jsonify({
            "success": True,
            "skill": roll["skill"],
            "difficulty": roll["difficulty"],
            "roll": result["roll"],
            "target": result["target"],
            "roll_success": result["success"],
            "message": result["message"],
            "narrative": narrative,
            "consequence": consequence,
            "empty": result.get("empty", False),
            "resources": gs.engine.resources_status(),
            "combat": gs.engine.combat_status(),
            "ending": gs.engine.ending_status(),
            "pending_roll": gs.pending_roll,
            "turn": gs.engine.state.turn,
            "location": gs.engine.state.location,
            "state": investigator_stats(gs.investigator)
        })
    except Exception as e:
        logger.warning("execute_roll failed for sid=%s", gs.sid, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/game/flee', methods=['POST'])
@synchronized
def flee_combat(gs):
    """Break off the current fight (the enemy gets one free attack)."""
    if not ctx().ensure_engine(gs) or not gs.investigator:
        return jsonify({"error": "Game not started"}), 400
    if not gs.engine.state.active_combat:
        return jsonify({"error": "Not in combat"}), 400
    try:
        res = gs.engine.attempt_flee()
        gs.pending_roll = None
        ctx().autosave(gs)
        return jsonify({
            "success": True,
            "narrative": res.get("narrative", ""),
            "combat": gs.engine.combat_status(),
            "pending_roll": None,
            "turn": gs.engine.state.turn,
            "location": gs.engine.state.location,
            "state": investigator_stats(gs.investigator)
        })
    except Exception as e:
        logger.warning("flee failed for sid=%s", gs.sid, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/game/reset', methods=['POST'])
@synchronized
def reset_game(gs):
    """Reset this session's game to start, releasing its resources."""
    if gs.engine and gs.engine.state:
        try:
            gs.engine.export_playtest("reset")
        except Exception:
            logger.warning("playtest export on reset failed", exc_info=True)
    ctx().cleanup_session(gs)
    gs.engine = None
    gs.investigator = None
    gs.pending_roll = None
    try:
        GenerativeSave.delete(gs.sid)
    except Exception:
        logger.warning("save delete failed for sid=%s", gs.sid, exc_info=True)

    return jsonify({"success": True, "message": "Game reset"})
