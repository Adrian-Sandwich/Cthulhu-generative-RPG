#!/usr/bin/env python3
"""
Token-gated monitoring dashboard.

Separate from the game routes because these read aggregate state across every
session and every save, not one player's game — and because they are the only
routes with access control, which is where authorization bugs live.
"""

import hmac
import json
import logging
import os

from flask import Blueprint, jsonify, render_template, request

from web.context import ctx

logger = logging.getLogger(__name__)

bp = Blueprint("admin", __name__)


def _admin_authorized() -> bool:
    return bool(ctx().admin_token) and hmac.compare_digest(
        request.args.get("token", ""), ctx().admin_token)


def _playtest_stats() -> dict:
    import glob
    sessions = []
    for p in glob.glob(str(ctx().data_dir / "saves" / "generative" / "*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        st = d.get("game_state", {})
        inv = st.get("investigator", {})
        narr = st.get("narrative", [])
        acts = [l for l in narr if l.startswith("Player:")]
        tele = st.get("telemetry") or {}
        offered = tele.get("rolls_from_dm", 0) + tele.get("rolls_synthesized", 0)
        sessions.append({
            "name": inv.get("name", "?"),
            "actions": len(acts),
            "turn": st.get("turn", 0),
            "rolls_offered": offered,
            "rolls_thrown": tele.get("rolls_thrown", 0),
            "rolls_synthesized": tele.get("rolls_synthesized", 0),
            # The two readings, per session. See GenerativeGameEngine.
            "mechanic_silent": len(acts) >= 5 and offered == 0,
            "dice_undiscovered": offered >= 2 and tele.get("rolls_thrown", 0) == 0,
            "san": inv.get("characteristics", {}).get("SAN", 99),
            "hp": inv.get("characteristics", {}).get("HP", 0),
            "location": st.get("location", "?"),
            "ending": st.get("ending_reached"),
            "mtime": os.path.getmtime(p),
        })
    real = [s for s in sessions if s["name"].strip().lower() not in ctx().exclude_names]
    played = [s for s in real if s["actions"] > 0]
    real.sort(key=lambda s: (-s["actions"], -s["mtime"]))

    feedback = []
    fb = ctx().data_dir / "feedback" / "feedback.jsonl"
    if fb.exists():
        with open(fb, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        feedback.append(json.loads(line))
                    except Exception:
                        pass
    ratings = [f["rating"] for f in feedback if f.get("rating")]

    # Playtest readings across real players. These exist to separate "the
    # mechanic never fires" from "the player never finds it" — with four
    # testers those were indistinguishable by hand.
    telemetry = {
        "sessions_with_rolls_offered": sum(1 for s in real if s["rolls_offered"]),
        "sessions_mechanic_silent": sum(1 for s in real if s["mechanic_silent"]),
        "sessions_dice_undiscovered": sum(1 for s in real if s["dice_undiscovered"]),
        "rolls_offered": sum(s["rolls_offered"] for s in real),
        "rolls_thrown": sum(s["rolls_thrown"] for s in real),
        "rolls_synthesized": sum(s["rolls_synthesized"] for s in real),
    }
    offered = telemetry["rolls_offered"]
    # Share of offered dice the players actually threw.
    telemetry["throw_rate"] = (
        round(telemetry["rolls_thrown"] / offered, 2) if offered else None)
    # Share of rolls the DM asked for itself, rather than the engine having
    # to inject one because the model ignored the roll protocol.
    telemetry["dm_roll_compliance"] = (
        round((offered - telemetry["rolls_synthesized"]) / offered, 2)
        if offered else None)

    return {
        "active_sessions": len(ctx().sessions),
        "total_saves": len(sessions),
        "telemetry": telemetry,
        "players": len(real),
        "played": len(played),
        "opened_only": len(real) - len(played),
        "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
        "feedback_count": len(feedback),
        "sessions": real[:40],
        "feedback": feedback[-20:],
    }


@bp.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    if not _admin_authorized():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(_playtest_stats())


@bp.route("/admin", methods=["GET"])
def admin_dashboard():
    if not _admin_authorized():
        return "Unauthorized — append ?token=YOUR_ADMIN_TOKEN", 401
    return render_template("admin.html", token=request.args.get("token", ""))
