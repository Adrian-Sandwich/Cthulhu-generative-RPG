#!/usr/bin/env python3
"""
Fast smoke/regression suite — no Ollama, no network. Mocks the LLM and drives
the real Flask app + engine to catch regressions in the hot path and the
safety guards. Run: pytest tests/test_smoke.py -q
"""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- fixtures --------------------------------------------------------------

@pytest.fixture
def client(tmp_path):
    """A fresh app client with storage redirected to a temp dir and the LLM
    mocked to a canned, tag-rich response."""
    os.environ["DATA_DIR"] = str(tmp_path)
    import importlib
    import app as app_module
    importlib.reload(app_module)

    def fake_chat(self, *a, **k):
        on = k.get("on_chunk")
        txt = "You press deeper into the dark. Something stirs."
        if on:
            on(txt)
        return txt

    def fake_tools(self, *a, **k):
        return {"narrative": "", "tool_calls": [], "fallback": True}

    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools", fake_tools):
        yield app_module.app.test_client()


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
    os.environ["DATA_DIR"] = str(tmp_path)
    import importlib, app as app_module
    importlib.reload(app_module)

    def fake_chat(self, *a, **k):
        if k.get("on_chunk"):
            k["on_chunk"]("ok")
        return "ok"
    with patch("core.llm_client.LLMClient.chat", fake_chat), \
         patch("core.llm_client.LLMClient.chat_with_tools",
               lambda *a, **k: {"narrative": "", "tool_calls": [], "fallback": True}):
        c1 = app_module.app.test_client()
        c2 = app_module.app.test_client()
        c1.post("/api/game/start", json={"name": "Alice", "archetype": "scholar"})
        c2.post("/api/game/start", json={"name": "Bob", "archetype": "detective"})
        n1 = c1.get("/api/game/state").get_json()["investigator"]["name"]
        n2 = c2.get("/api/game/state").get_json()["investigator"]["name"]
        assert n1 == "Alice" and n2 == "Bob"


# --- engine units ----------------------------------------------------------

def test_save_id_sanitized():
    from core.generative_save import GenerativeSave, SAVES_DIR
    from pathlib import Path
    p = GenerativeSave._save_path("../../etc/passwd")
    assert p.name == "etcpasswd.json"
    assert p.resolve().parent == Path(SAVES_DIR).resolve()


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
    e = GenerativeGameEngine(model="mistral", use_memory=False, session_id="u3")
    e.create_game(create_investigator("T", "scholar"))
    start = e.state.location
    with patch.object(e, "_call_ollama", return_value="You wonder about the hidden chamber above."):
        e.process_player_action("what is up there?")
    assert e.state.location == start  # mere mention must not teleport
