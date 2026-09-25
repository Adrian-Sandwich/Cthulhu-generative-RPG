"""Durable action receipts, committed atomically with the game's autosave.

All writers hold the session lock (also a PostgreSQL advisory lock when
configured). Receipts live for the lifetime of a game; they must not be
evicted, or an old action ID could execute again.
"""

import logging
import re
from copy import deepcopy
from uuid import uuid4

from core.moderation import is_allowed
from core.dm_guardrails import action_allowed
from core.world_rules import inventory_query

logger = logging.getLogger(__name__)
ID_PATTERN = re.compile(r'[A-Za-z0-9_-]{8,128}\Z')


def validate_action(data, game):
    if not isinstance(data, dict):
        return None, ({'error': 'Expected a JSON object'}, 400)
    text = data.get('action', '')
    if not isinstance(text, str) or not text.strip():
        return None, ({'error': 'Action cannot be empty'}, 400)
    if len(text) > game.max_action_len:
        return None, ({'error': 'Action too long'}, 413)
    if not action_allowed(text):
        return None, ({'error': 'Describe what your investigator attempts. Rules, rewards and dice are decided by the game.'}, 422)
    if not is_allowed(text):
        return None, ({'error': "That action can't be processed."}, 422)
    action_id = data.get('action_id', uuid4().hex)
    if not isinstance(action_id, str) or not ID_PATTERN.fullmatch(action_id):
        return None, ({'error': 'Invalid action_id'}, 400)
    game_id = data.get('game_id')
    if 'action_id' in data and game_id is None:
        return None, ({'error': 'game_id is required with action_id'}, 400)
    if game_id is not None and (not isinstance(game_id, str) or not ID_PATTERN.fullmatch(game_id)):
        return None, ({'error': 'Invalid game_id'}, 400)
    return {'action': text, 'action_id': action_id, 'game_id': game_id}, None


def prepare_action(game, gs, command):
    """Return an existing response or persist a checkpoint before execution."""
    if not game.ensure_engine(gs) or not gs.investigator:
        if game.has_save(gs):
            return {'error': 'Could not restore the saved game. Please retry.'}, 503
        return {'error': 'Game not started'}, 400
    if command['game_id'] is not None and command['game_id'] != gs.game_id:
        return {'error': 'This action belongs to a different game'}, 409
    action_id = command['action_id']
    record = gs.actions.get(action_id)
    if record:
        if record['action'] != command['action']:
            return {'error': 'action_id already used for a different action'}, 409
        if record['status'] in ('pending', 'running'):
            # The caller holds the session lock, so no worker can still own
            # this receipt. Recover an orphan (e.g. thread creation failed).
            game.cleanup_session(gs)
            gs.engine = None
            if not game.ensure_engine(gs):
                return {'error': 'Could not restore the interrupted turn'}, 503
            record = gs.actions[action_id]
        return record['result'], record['http_status']
    if gs.pending_roll and not inventory_query(command['action']):
        return {'error': 'Resolve the pending roll first'}, 409
    gs.actions[action_id] = {'action': command['action'], 'status': 'pending'}
    try:
        game.autosave(gs, strict=True)
        gs.actions[action_id]['status'] = 'running'
        game.autosave(gs, strict=True)
    except Exception:
        # No engine work has happened. Reload the last durable checkpoint,
        # including a failed receipt if the pending write had succeeded.
        game.cleanup_session(gs)
        gs.engine = None
        game.ensure_engine(gs)
        return {'error': 'Could not persist the turn. Please check its status.',
                'action_id': action_id, 'game_id': gs.game_id}, 503
    return None


def execute_action(game, gs, command, finalize, on_chunk=None):
    action_id = command['action_id']
    rejected = False
    try:
        result = gs.engine.process_player_action(command['action'], on_chunk=on_chunk)
        if result.get('error'):
            rejected = True
            raise ValueError(result['error'])
        payload = finalize(gs, result, game, persist=False)
        payload.update(action_id=action_id, game_id=gs.game_id)
        gs.actions[action_id].update(status='completed', result=deepcopy(payload), http_status=200)
        # Receipt and all mechanics become visible in the same atomic replace.
        game.autosave(gs, strict=True)
        return payload, 200
    except Exception as exc:
        logger.warning('turn failed for sid=%s action=%s', gs.sid, action_id, exc_info=True)
        game.cleanup_session(gs)
        gs.engine = None
        # The checkpoint contains the pre-turn state. A failed or interrupted
        # turn never leaves partially applied mechanics available to the next.
        restored = game.ensure_engine(gs)
        payload = {'error': str(exc), 'action_id': action_id, 'game_id': gs.game_id}
        status = 503 if isinstance(exc, OSError) or not restored else (400 if rejected else 500)
        if restored:
            gs.actions[action_id].update(status='failed', result=payload, http_status=status)
            try:
                game.autosave(gs, strict=True)
            except Exception:
                status = 503
        return payload, status
