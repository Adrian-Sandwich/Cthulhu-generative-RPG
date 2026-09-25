#!/usr/bin/env python3
"""
Routes that need a player session and its engine.

Mutations serialize on each player's lock. Action status reads can inspect
the atomic autosave while a model call is still running.
"""

import json as _json
import logging
import queue as _queue
import threading as _threading
from contextvars import copy_context
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, Response, jsonify, request

from core.archetypes import ARCHETYPES, create_investigator
from core.generative_save import GenerativeSave
from core.game_generative import GenerativeGameEngine
from core.world_rules import available_actions, journal
from core.moderation import is_allowed
from core.postgres_store import StorageUnavailable
from web.context import ctx, investigator_stats, rate_limited, synchronized
from web.turns import ID_PATTERN, validate_action, prepare_action, execute_action

logger = logging.getLogger(__name__)

bp = Blueprint("game", __name__)


@bp.route('/api/game/start', methods=['POST'])
@rate_limited('start')
@synchronized
def start_game(gs):
    """Start a new game"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Expected a JSON object"}), 400
    investigator_name = data.get('name', 'Unknown Investigator')
    occupation = data.get('archetype', 'scholar')
    if not isinstance(investigator_name, str) or not investigator_name.strip() or len(investigator_name) > 100:
        return jsonify({"error": "Name must contain 1 to 100 characters"}), 400
    if not isinstance(occupation, str) or occupation not in ARCHETYPES:
        return jsonify({"error": "Unknown archetype"}), 400
    # Spanish paused again by request — force English regardless of client.
    language = 'en'

    try:
        if gs.engine:
            ctx().cleanup_session(gs)
        gs.pending_roll = None
        gs.game_id = uuid4().hex
        gs.actions = {}

        gs.investigator = create_investigator(investigator_name, occupation)

        gs.engine = GenerativeGameEngine(use_memory=False, session_id=gs.sid,
                                         language=language, data_dir=ctx().data_dir)
        gs.engine.save_store = gs.store
        gs.engine.create_game(gs.investigator)

        intro = gs.engine.localized_intro()

        ctx().autosave(gs)

        return jsonify({
            "success": True,
            "game_id": gs.game_id,
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
    except StorageUnavailable:
        raise
    except Exception as e:
        logger.warning("start_game failed for sid=%s", gs.sid, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/game/saves', methods=['GET'])
@synchronized
def list_saves(gs):
    """List saved games for this session (currently a single autosave per sid)."""
    summary = GenerativeSave.get_session_summary(gs.sid, ctx().data_dir, store=gs.store)
    return jsonify({"saves": [summary] if summary else []})


@bp.route('/api/game/load', methods=['POST'])
@rate_limited('start')
@synchronized
def load_saved_game(gs):
    """Resume this session's autosaved game from disk."""
    if not ctx().has_save(gs):
        return jsonify({"error": "No saved game for this session"}), 404
    if gs.engine:
        ctx().cleanup_session(gs)
        gs.engine = None
    if not ctx().ensure_engine(gs):
        return jsonify({"error": "Could not load saved game"}), 500
    return jsonify({
        "success": True,
        "game_id": gs.game_id,
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
        "world_actions": available_actions(gs.engine),
        "discoveries": journal(gs.engine),
        "ending": gs.engine.ending_status() if gs.engine.state.ending_reached else None,
        "location": gs.engine.state.location,
        "game_id": gs.game_id,
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
            "maxHP": inv.characteristics.get('max_hp', inv.characteristics['HP']),
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
    """Execute once, or return the receipt for a repeated action ID."""
    command, error = validate_action(request.get_json(silent=True), ctx())
    if error:
        return jsonify(error[0]), error[1]
    previous = prepare_action(ctx(), gs, command)
    payload, status = previous or execute_action(ctx(), gs, command, _finalize_turn)
    return jsonify(payload), status


def _finalize_turn(gs, result, game=None, persist=True):
    """Apply a turn's consequences and build the response payload."""
    outcome = ({'events': [], 'pending_roll': None} if result.get('read_only')
               else gs.engine.apply_turn_consequences(result))
    if outcome["pending_roll"] and not gs.pending_roll:
        gs.pending_roll = outcome["pending_roll"]

    if gs.engine.state.ending_reached:
        try:
            gs.engine.export_playtest("ending")
        except Exception:
            logger.warning("playtest export on ending failed", exc_info=True)

    if persist:
        (game or ctx()).autosave(gs)

    narrative = result.get("narrative", "")
    if narrative and not is_allowed(narrative):
        narrative = "The scene blurs; your mind refuses to hold what you just perceived."

    return {
        "success": True,
        "game_id": gs.game_id,
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
    command, error = validate_action(request.get_json(silent=True), ctx())
    if error:
        return jsonify(error[0]), error[1]

    # Bind the context here, in request scope. The generator below runs after
    # Flask has torn the request context down, so anything resolved through
    # current_app inside it raises "Working outside of request context" — the
    # same failure mode that made this endpoint 500 on every real turn when it
    # reached for request.is_disconnected.
    game = ctx()

    def _stream():
        with game.session_scope(gs):
            previous = prepare_action(game, gs, command)
            if previous:
                payload, status = previous
                event = 'done' if status == 200 else 'error'
                if status == 503:
                    payload = dict(payload, retry_status=True)
                yield f"event: {event}\ndata: {_json.dumps(payload)}\n\n"
                return

            q = _queue.Queue(maxsize=64)
            holder = {}
            cancel_event = _threading.Event()
            completed = _threading.Event()

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
                    holder['response'] = execute_action(game, gs, command, _finalize_turn, on_chunk)
                except StorageUnavailable:
                    holder['response'] = ({'error': 'Game storage is temporarily unavailable'}, 503)
                finally:
                    completed.set()
                    # Wake an idle consumer immediately after the durable
                    # result is ready. Completion remains independent of queue
                    # capacity, including a disconnected or slow consumer.
                    try:
                        q.put_nowait(None)
                    except _queue.Full:
                        pass

            worker_context = copy_context()
            worker_thread = _threading.Thread(target=worker_context.run, args=(worker,), daemon=True)
            worker_thread.start()

            try:
                while True:
                    if completed.is_set() and q.empty():
                        break
                    try:
                        chunk = q.get(timeout=1.0)
                    except _queue.Empty:
                        # Completion is separate from chunk delivery: a full
                        # queue must not lose the terminal result or error.
                        if completed.is_set():
                            break
                        continue
                    if chunk is None:
                        break
                    yield f"data: {_json.dumps({'chunk': chunk})}\n\n"
            finally:
                cancel_event.set()
                worker_thread.join()

            payload, status = holder['response']
            event = 'done' if status == 200 else 'error'
            if status == 503:
                payload = dict(payload, retry_status=True)
            yield f"event: {event}\ndata: {_json.dumps(payload)}\n\n"

    def stream():
        try:
            yield from _stream()
        except StorageUnavailable:
            yield 'event: error\ndata: {"error": "Game storage is temporarily unavailable", "retry_status": true}\n\n'

    return Response(stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@bp.route('/api/game/actions/<action_id>', methods=['GET'])
def get_action_status(action_id):
    """Read durable progress without waiting behind an in-flight model call."""
    if not ID_PATTERN.fullmatch(action_id):
        return jsonify({'error': 'Invalid action_id'}), 400
    game = ctx()
    gs = game.get_session()
    with game.session_scope(gs, blocking=False) as acquired:
        if acquired:
            if not game.ensure_engine(gs):
                if game.has_save(gs):
                    return jsonify({'error': 'Saved game temporarily unavailable'}), 503
                return jsonify({'error': 'Game not started'}), 404
            state = {'game_id': gs.game_id, 'actions': gs.actions}
        else:
            state = GenerativeSave.load_app_state(gs.sid, game.data_dir, store=game.store) or {}
        expected_game = request.args.get('game_id')
        if expected_game and expected_game != state.get('game_id'):
            return jsonify({'error': 'This action belongs to a different game'}), 409
        record = state.get('actions', {}).get(action_id)
        if record is None:
            return jsonify({'error': 'Action not found'}), 404
        return jsonify(dict(record, action_id=action_id, game_id=state.get('game_id')))


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
            "game_id": gs.game_id,
        "turn": gs.engine.state.turn,
            "location": gs.engine.state.location,
            "state": investigator_stats(gs.investigator)
        })
    except StorageUnavailable:
        raise
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
            "game_id": gs.game_id,
        "turn": gs.engine.state.turn,
            "location": gs.engine.state.location,
            "state": investigator_stats(gs.investigator)
        })
    except StorageUnavailable:
        raise
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
    gs.actions = {}
    gs.game_id = uuid4().hex
    try:
        GenerativeSave.delete(gs.sid, ctx().data_dir, store=gs.store)
    except StorageUnavailable:
        raise
    except Exception:
        logger.warning("save delete failed for sid=%s", gs.sid, exc_info=True)

    return jsonify({"success": True, "message": "Game reset"})
