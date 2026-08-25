#!/usr/bin/env python3
"""
Unit tests for core engine mechanics — no LLM, no Ollama, no network.
Run: pytest tests/test_engine_units.py -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game_generative import GenerativeGameEngine
from core.state import InvestigatorState
from core.archetypes import create_investigator


def _fresh_engine(session_id):
    """Build an engine with memory/entity_graph disabled so nothing external runs."""
    return GenerativeGameEngine(
        model="mistral",
        use_memory=False,
        use_entity_graph=False,
        session_id=session_id,
    )


@pytest.fixture
def engine(tmp_path):
    """Engine with a fresh game and temp save dir."""
    os.environ["DATA_DIR"] = str(tmp_path)
    e = _fresh_engine(f"unit_{tmp_path.name}")
    e.create_game(create_investigator("Tester", "scholar"))
    return e


# --- inventory ---------------------------------------------------------------

def test_pick_up_item_adds_to_inventory(engine):
    assert "Revolver (.38)" not in engine.state.investigator.inventory
    msg = engine.pick_up_item("revolver")
    assert "Revolver (.38)" in engine.state.investigator.inventory
    assert "loaded" in msg or "pick up" in msg


def test_pick_up_item_already_owned(engine):
    engine.pick_up_item("revolver")
    msg = engine.pick_up_item("revolver")
    assert "already have" in msg


def test_pick_up_unknown_item(engine):
    assert "not found" in engine.pick_up_item("nonexistent").lower()


def test_drop_item(engine):
    engine.pick_up_item("rope")
    assert "Rope (30ft)" in engine.state.investigator.inventory
    msg = engine.drop_item("Rope (30ft)")
    assert "Rope (30ft)" not in engine.state.investigator.inventory
    assert "drop" in msg


def test_use_item_flashlight(engine):
    engine.state.investigator.inventory.append("Flashlight")
    msg = engine.use_item("Flashlight")
    assert "beam" in msg.lower()


# --- combat ------------------------------------------------------------------

def test_start_combat_sets_enemy(engine):
    res = engine.start_combat("deep_one_hybrid")
    assert "error" not in res
    assert engine.state.active_combat["name"] == "Deep One Hybrid"
    assert engine.state.game_phase == "combat"


def test_start_combat_unknown_enemy(engine):
    res = engine.start_combat("cthulhu")
    assert "error" in res


def test_resolve_combat_round_player_wins(engine):
    engine.start_combat("deep_one_hybrid")
    # Guarantee the kill regardless of the random damage roll.
    engine.state.active_combat["hp"] = 4
    res = engine.resolve_combat_round(player_roll_success=True, critical="CRITICAL SUCCESS")
    assert res["combat_over"]
    assert res["enemy_dead"]
    assert engine.state.active_combat is None
    assert engine.state.game_phase == "exploring"


def test_resolve_combat_round_player_dies(engine):
    engine.start_combat("deep_one_hybrid")
    engine.state.investigator.characteristics["HP"] = 1
    # Force enemy hit and high damage by using crit failure.
    res = engine.resolve_combat_round(player_roll_success=False, critical="CRITICAL FAILURE")
    assert res["combat_over"]
    assert res["player_dead"]
    assert engine.state.ending_reached == "death"


def test_combat_attack_roll_uses_firearm_when_loaded(engine):
    engine.pick_up_item("revolver")
    pending = engine.combat_attack_roll()
    assert pending["skill"] == "firearms_revolver"
    assert pending.get("combat") is True


# --- sanity / hp -------------------------------------------------------------

def test_apply_sanity_check_reduces_san(engine):
    before = engine.state.investigator.characteristics["SAN"]
    res = engine.apply_sanity_check(5)
    after = engine.state.investigator.characteristics["SAN"]
    assert after == before - 5
    assert res["sanity_remaining"] == after


def test_apply_sanity_check_clamped(engine):
    before = engine.state.investigator.characteristics["SAN"]
    res = engine.apply_sanity_check(999)
    assert engine.state.investigator.characteristics["SAN"] == max(0, before - 30)


def test_apply_hp_damage_reduces_hp(engine):
    before = engine.state.investigator.characteristics["HP"]
    res = engine.apply_hp_damage(3)
    after = engine.state.investigator.characteristics["HP"]
    assert after == before - 3
    assert res["state"] == "WOUNDED"


def test_apply_hp_damage_death_ending(engine):
    engine.state.investigator.characteristics["HP"] = 2
    res = engine.apply_hp_damage(5)
    assert res["state"] == "DEAD"
    assert engine.state.ending_reached == "death"


# --- save / load -------------------------------------------------------------

def test_save_and_load_roundtrip(engine, tmp_path):
    engine.pick_up_item("revolver")
    engine.start_combat("deep_one_hybrid")
    engine.apply_hp_damage(2)

    path = engine.save_game()
    assert os.path.exists(path)

    loaded = GenerativeGameEngine.load_game(engine.session_id)
    assert loaded.state.investigator.name == engine.state.investigator.name
    assert "Revolver (.38)" in loaded.state.investigator.inventory
    assert loaded.state.active_combat is not None
    assert loaded.state.investigator.characteristics["HP"] == engine.state.investigator.characteristics["HP"]


# --- endings -----------------------------------------------------------------

def test_check_ending_hp_zero(engine):
    engine.state.investigator.characteristics["HP"] = 0
    assert engine.check_ending_condition() == "death"


def test_check_ending_san_zero(engine):
    engine.state.investigator.characteristics["SAN"] = 0
    assert engine.check_ending_condition() == "madness"


def test_check_ending_no_ending(engine):
    assert engine.check_ending_condition() is None


# --- location resolution -----------------------------------------------------
# Regression guard: the [LOCATION: name] tag path had its resolver deleted by the
# module-extraction refactor while the call site survived, so every DM-tagged
# move raised AttributeError (HTTP 500 for the player). The tag is the only
# language-independent way to move, so this path must stay covered.

def _cfg():
    from core.adventure_config import AdventureConfig
    return AdventureConfig.from_name("point_black")


def test_resolve_location_by_key():
    assert _cfg().resolve_location("keeper_quarters") == "Keeper's Quarters"


def test_resolve_location_by_display_name():
    assert _cfg().resolve_location("Keeper's Quarters") == "Keeper's Quarters"


def test_resolve_location_case_and_whitespace_insensitive():
    assert _cfg().resolve_location("  KEEPER'S QUARTERS  ") == "Keeper's Quarters"


def test_resolve_location_substring_fallback():
    # "the Lantern Room" is not an exact key or name, but contains one.
    assert _cfg().resolve_location("the Lantern Room") == "Lantern Room"


def test_resolve_location_empty_is_none():
    assert _cfg().resolve_location("") is None
    assert _cfg().resolve_location("   ") is None


def test_resolve_location_invented_place_rejected():
    # World containment: the DM inventing an off-map place must not resolve.
    assert _cfg().resolve_location("Village Library") is None
    assert _cfg().resolve_location("Police Station") is None


def test_dm_location_tag_moves_player(engine):
    from unittest.mock import patch
    start = engine.state.location
    assert start != "Keeper's Quarters"
    dm = "You climb the stairs into the keeper's room. [LOCATION: Keeper's Quarters]"
    with patch.object(engine, "_call_ollama", return_value=dm):
        engine.process_player_action("go up to the keeper's quarters")
    assert engine.state.location == "Keeper's Quarters"


def test_dm_invented_location_tag_ignored(engine):
    from unittest.mock import patch
    start = engine.state.location
    dm = "You walk into town and enter the library. [LOCATION: Village Library]"
    with patch.object(engine, "_call_ollama", return_value=dm):
        engine.process_player_action("go to the village library")
    assert engine.state.location == start


def test_all_dm_tags_survive_a_turn(engine):
    """Every tag in tag_parser._TAG_PATTERNS must survive a full turn.

    This is the class-level guard: an orphaned call site on any tag path fails
    here instead of reaching a player as a 500. ENDING goes in a second turn
    because it terminates the game.
    """
    from unittest.mock import patch
    from core.tag_parser import _TAG_PATTERNS

    dm = (
        "The dark presses in and something moves below. "
        "[ROLL: spot hidden/Hard] [SANITY_CHECK: 2] [ITEM_FOUND: revolver] "
        "[HP_DAMAGE: 1] [AMMO_FOUND: 2] [NPC_DIALOGUE: warner] "
        "[COMBAT_START: deep_one_hybrid] [LOCATION: Keeper's Quarters]"
    )
    dm_ending = "The boat pulls away from the rocks. [ENDING: escape]"

    # Completeness: if a new tag is added to the parser, this test must grow.
    for tag in _TAG_PATTERNS:
        assert f"[{tag}" in dm + dm_ending, f"tag {tag} not exercised by this test"

    with patch.object(engine, "_call_ollama", return_value=dm):
        result = engine.process_player_action("search the room")
    outcome = engine.apply_turn_consequences(result)

    assert "error" not in result
    assert isinstance(outcome.get("events"), list)
    assert engine.state.location == "Keeper's Quarters"
    assert "Revolver (.38)" in engine.state.investigator.inventory

    with patch.object(engine, "_call_ollama", return_value=dm_ending):
        engine.process_player_action("row for the shore")
    assert engine.state.ending_reached == "escape"


# --- DM prompt state ---------------------------------------------------------
# The prompt reports "Companions Alive: N" to the model. That read used to point
# at a `companion_manager` attribute the engine does not have, guarded by
# getattr, so it always reported 0 while the same prompt separately described
# the allies by name — contradictory data, and silent.

def test_prompt_reports_recruited_companions(engine):
    engine.companions.recruit_custom("warner", "Lt. William Warner", "Coast Guard")
    assert len(engine.companions.get_active_companions()) == 1

    prompt = engine._build_dm_prompt("look around")
    assert "Companions Alive: 1" in prompt, prompt[-500:]


def test_prompt_reports_zero_companions_when_alone(engine):
    prompt = engine._build_dm_prompt("look around")
    assert "Companions Alive: 0" in prompt


def test_prompt_companion_lines_agree(engine):
    """The count and the narrative description must not contradict each other."""
    engine.companions.recruit_custom("warner", "Lt. William Warner", "Coast Guard")
    prompt = engine._build_dm_prompt("look around")
    assert "Companions Alive: 1" in prompt
    assert "You are alone." not in prompt
    assert "Warner" in prompt
