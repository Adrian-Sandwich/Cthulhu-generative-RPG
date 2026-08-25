#!/usr/bin/env python3
"""
Fast smoke/regression suite — no Ollama, no network. Mocks the LLM and drives
a fresh Flask app instance per test to catch regressions in the hot path and
the safety guards. Run: pytest tests/test_smoke.py -q
"""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- fixtures --------------------------------------------------------------

def _make_app(data_dir):
    """Build a fresh app instance isolated to the given data directory."""
    import app as app_module
    return app_module.create_app({"DATA_DIR": str(data_dir)})


# A canned DM reply that actually carries mechanic tags. The tags matter: the
# [LOCATION: name] path lost its resolver in a refactor and shipped broken
# because this fixture claimed to be "tag-rich" while returning bare prose, so
# nothing exercised it. Terminal tags (ROLL, COMBAT_START, ENDING) stay out —
# they would change game phase for every test sharing this fixture.
CANNED_DM = (
    "You press deeper into the dark. Something stirs. "
    "[LOCATION: Keeper's Quarters] [ITEM_FOUND: revolver]"
)


@pytest.fixture
def client(tmp_path):
    """A fresh app client with storage redirected to a temp dir and the LLM
    mocked to a canned, genuinely tag-rich response (see CANNED_DM)."""

    def fake_chat(self, *a, **k):
        on = k.get("on_chunk")
        txt = CANNED_DM
        if on:
            on(txt)
        return txt

    def fake_tools(self, *a, **k):
        return {"narrative": "", "tool_calls": [], "fallback": True}

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools", fake_tools):
        yield _make_app(tmp_path).test_client()


def _start(client, **kw):
    body = {"name": "Tester", "archetype": "scholar"}
    body.update(kw)
    return client.post("/api/game/start", json=body)


# --- core flow -------------------------------------------------------------

def test_start_and_state(client):
    r = _start(client)
    assert r.status_code == 200 and r.get_json()["success"]
    s = client.get("/api/game/state").get_json()
    assert s["turn"] == 1
    assert s["location"]


def test_action_turn(client):
    _start(client)
    r = client.post("/api/game/action", json={"action": "look around the room"})
    assert r.status_code == 200
    assert r.get_json()["success"]


def test_dm_tags_take_mechanical_effect_over_http(client):
    """The tags in CANNED_DM must change real state, not just parse.

    Regression: [LOCATION: name] used to raise AttributeError inside
    process_player_action, which app.py turns into a 500 — so the most common
    player action (moving) lost the turn.
    """
    _start(client)
    before = client.get("/api/game/state").get_json()
    assert before["location"] != "Keeper's Quarters"

    r = client.post("/api/game/action", json={"action": "go up to the keeper's quarters"})
    assert r.status_code == 200, r.get_data(as_text=True)

    after = client.get("/api/game/state").get_json()
    assert after["location"] == "Keeper's Quarters"
    assert "Revolver (.38)" in after["investigator"]["inventory"]


def test_action_stream(client):
    _start(client)
    r = client.post("/api/game/action/stream", json={"action": "look around the room"})
    assert r.status_code == 200
    assert r.mimetype == "text/event-stream"
    data = r.get_data(as_text=True)
    assert "data:" in data
    assert "event: done" in data


def test_action_stream_survives_a_slow_first_chunk(tmp_path):
    """The SSE generator must survive the queue-timeout branch.

    Regression: that branch read `request.is_disconnected` — an attribute Flask
    does not have, on a proxy that is unbound once the request context tears
    down — so it raised RuntimeError and the stream 500'd, silently degrading
    every turn to the non-streaming fallback. The default fixture's LLM answers
    instantly, so `q.get(timeout=1.0)` never times out and the branch was
    unreachable. This one makes the model slow enough to reach it.
    """
    import time

    def slow_chat(self, *a, **k):
        on = k.get("on_chunk")
        time.sleep(1.6)          # longer than the generator's 1.0s queue timeout
        if on:
            on(CANNED_DM)
        return CANNED_DM

    with patch("core.llm_client.LLMClient.chat", slow_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        c = _make_app(tmp_path).test_client()
        c.post("/api/game/start", json={"name": "Slow", "archetype": "scholar"})
        r = c.post("/api/game/action/stream", json={"action": "listen at the door"})
        assert r.status_code == 200
        data = r.get_data(as_text=True)

    assert "event: done" in data, data[-400:]
    assert "Working outside of request context" not in data
    assert "event: error" not in data, data[-400:]


def test_roll_flow(client):
    _start(client)
    r = client.post("/api/game/action", json={"action": "climb the slick cliff"}).get_json()
    if r.get("pending_roll"):
        rr = client.post("/api/game/roll").get_json()
        assert rr["success"] and "roll" in rr


def test_reset(client):
    _start(client)
    assert client.post("/api/game/reset").get_json()["success"]


# --- input guards ----------------------------------------------------------

def test_empty_action_400(client):
    _start(client)
    assert client.post("/api/game/action", json={"action": "   "}).status_code == 400


def test_oversized_action_413(client):
    _start(client)
    assert client.post("/api/game/action", json={"action": "a" * 5000}).status_code == 413


def test_bad_json_no_500(client):
    _start(client)
    r = client.post("/api/game/action", data="not json", content_type="text/plain")
    assert r.status_code < 500


def test_moderation_blocks_input(client):
    _start(client)
    assert client.post("/api/game/action", json={"action": "child porn"}).status_code == 422


def test_moderation_allows_horror(client):
    _start(client)
    r = client.post("/api/game/action", json={"action": "I stab the creature, blood everywhere"})
    assert r.status_code == 200


# --- session isolation -----------------------------------------------------

def test_two_clients_isolated(tmp_path):
    def fake_chat(self, *a, **k):
        if k.get("on_chunk"):
            k["on_chunk"]("ok")
        return "ok"

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        c1 = _make_app(tmp_path).test_client()
        c2 = _make_app(tmp_path).test_client()
        c1.post("/api/game/start", json={"name": "Alice", "archetype": "scholar"})
        c2.post("/api/game/start", json={"name": "Bob", "archetype": "detective"})
        n1 = c1.get("/api/game/state").get_json()["investigator"]["name"]
        n2 = c2.get("/api/game/state").get_json()["investigator"]["name"]
        assert n1 == "Alice" and n2 == "Bob"


# --- engine units ----------------------------------------------------------

def test_save_id_sanitized():
    from core.generative_save import GenerativeSave, saves_dir
    from pathlib import Path
    p = GenerativeSave._save_path("../../etc/passwd")
    assert p.name == "etcpasswd.json"
    assert p.resolve().parent == saves_dir().resolve()


def test_rel_type_whitelist():
    from core.entity_graph import EntityGraph
    g = EntityGraph.__new__(EntityGraph)
    g.enabled = False
    assert g.add_relationship("a", "EVIL_INJECT", "b") is False


def test_failure_consequence_scales():
    from core.game_generative import GenerativeGameEngine
    from core.archetypes import create_investigator
    e = GenerativeGameEngine(model="mistral", use_memory=False, session_id="u")
    e.create_game(create_investigator("T", "scholar"))
    small = e._failure_consequence({"skill": "climb", "roll": 55, "target": 50})
    fumble = e._failure_consequence({"skill": "climb", "roll": 99, "target": 50})
    assert small["kind"] == "hp" and fumble["fumble"] and fumble["amount"] >= small["amount"]


def test_ammo_and_firearm():
    from core.game_generative import GenerativeGameEngine
    from core.archetypes import create_investigator
    e = GenerativeGameEngine(model="mistral", use_memory=False, session_id="u2")
    e.create_game(create_investigator("T", "scholar"))
    assert e.state.ammo == 0 and e.resources_status()["has_firearm"] is False
    e.pick_up_item("revolver")
    assert e.state.ammo > 0 and e.resources_status()["has_firearm"] is True


def test_location_needs_movement():
    from core.game_generative import GenerativeGameEngine
    from core.archetypes import create_investigator
    from unittest.mock import patch
    e = GenerativeGameEngine(model="mistral", use_memory=False, session_id="u3")
    e.create_game(create_investigator("T", "scholar"))
    start = e.state.location
    with patch.object(e, "_call_ollama", return_value="You wonder about the hidden chamber above."):
        e.process_player_action("what is up there?")
    assert e.state.location == start  # mere mention must not teleport


# --- admin dashboard -------------------------------------------------------
# The only two endpoints with access control, and they had no coverage at all.
# Everything here is about the gate, not the numbers behind it.

def _admin_app(tmp_path, **cfg):
    import app as app_module
    return app_module.create_app({"DATA_DIR": str(tmp_path), **cfg}).test_client()


def test_admin_disabled_when_no_token_configured(tmp_path):
    """With ADMIN_TOKEN unset the dashboard must be closed, not open.

    `_admin_authorized` leads with `bool(ADMIN_TOKEN)`; if that guard were ever
    dropped, an empty configured token would compare equal to an empty query
    token and the dashboard would be world-readable.
    """
    c = _admin_app(tmp_path, ADMIN_TOKEN="")
    assert c.get("/admin").status_code == 401
    assert c.get("/admin?token=").status_code == 401
    assert c.get("/api/admin/stats?token=").status_code == 401
    assert c.get("/api/admin/stats").status_code == 401


def test_admin_rejects_wrong_token(tmp_path):
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret")
    for bad in ("", "wrong", "s3cre", "s3secret", "S3CRET", "s3cret "):
        assert c.get(f"/api/admin/stats?token={bad}").status_code == 401, bad
        assert c.get(f"/admin?token={bad}").status_code == 401, bad
    assert c.get("/api/admin/stats").status_code == 401


def test_admin_accepts_correct_token(tmp_path):
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret")

    r = c.get("/api/admin/stats?token=s3cret")
    assert r.status_code == 200
    body = r.get_json()
    for key in ("active_sessions", "total_saves", "players", "played",
                "opened_only", "feedback_count", "sessions", "feedback"):
        assert key in body, key

    page = c.get("/admin?token=s3cret")
    assert page.status_code == 200
    assert b"Unauthorized" not in page.data


def test_admin_unauthorized_page_explains_how(tmp_path):
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret")
    r = c.get("/admin")
    assert r.status_code == 401
    assert b"token" in r.data.lower()


def test_admin_stats_excludes_configured_names(tmp_path):
    """EXCLUDE_NAMES keeps the team's own sessions out of the playtest numbers."""
    c = _admin_app(tmp_path, ADMIN_TOKEN="s3cret", EXCLUDE_NAMES="Adrian, tester")

    saves = tmp_path / "saves" / "generative"
    saves.mkdir(parents=True)
    import json as _j

    def _save(name, actions):
        (saves / f"{name}.json").write_text(_j.dumps({
            "game_state": {
                "investigator": {"name": name, "characteristics": {"SAN": 60, "HP": 9}},
                "narrative": [f"Player: act {i}" for i in range(actions)],
                "turn": actions,
                "location": "Point Black Lighthouse - Exterior",
            }
        }))

    _save("Adrian", 5)      # excluded by name
    _save("tester", 3)      # excluded by name, case-insensitively
    _save("Pao", 4)         # counted, and played
    _save("Champi", 0)      # counted, opened only

    body = c.get("/api/admin/stats?token=s3cret").get_json()
    assert body["total_saves"] == 4          # every file is seen
    assert body["players"] == 2              # but only non-excluded ones count
    assert body["played"] == 1
    assert body["opened_only"] == 1
    names = {s["name"] for s in body["sessions"]}
    assert names == {"Pao", "Champi"}
