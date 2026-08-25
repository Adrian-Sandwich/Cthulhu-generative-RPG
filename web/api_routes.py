#!/usr/bin/env python3
"""
Routes that need no game state: archetype sheets, feedback, health.
"""

import json
import logging
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from core.archetypes import get_archetype_sheets
from web.context import ctx, rate_limited, synchronized

logger = logging.getLogger(__name__)

bp = Blueprint("api", __name__)


@bp.route('/api/archetypes', methods=['GET'])
def get_archetypes():
    """Archetype stat blocks for the character sheet preview"""
    return jsonify({"archetypes": get_archetype_sheets()})


@bp.route('/api/feedback', methods=['POST'])
@rate_limited('feedback')
@synchronized
def leave_feedback(gs):
    """Store player feedback, linked to their session."""
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
        fb_dir = ctx().data_dir / "feedback"
        fb_dir.mkdir(parents=True, exist_ok=True)
        with open(fb_dir / "feedback.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.warning("feedback write failed", exc_info=True)
        return jsonify({"error": "Could not save feedback"}), 500
    return jsonify({"success": True, "message": "Thank you, investigator."})


@bp.route('/api/health', methods=['GET'])
def health():
    """Liveness, plus whether the model is actually answering.

    "ok" used to mean only that Flask was up. Production once ran for weeks on
    a model the provider had retired: every turn 404'd, the engine swallowed it
    and served a canned sentence, and this endpoint kept saying ok. Reporting
    the degraded-turn counter makes that visible to anything that polls here.
    """
    from core.llm_client import LLMClient

    degraded = LLMClient.degraded_turns
    body = {
        "status": "degraded" if degraded else "ok",
        "sessions": len(ctx().sessions),
        "llm": {
            "model": os.environ.get("LLM_MODEL", "(default)"),
            "degraded_turns": degraded,
        },
    }
    if degraded:
        body["llm"]["last_error"] = LLMClient.last_error
    return jsonify(body)
