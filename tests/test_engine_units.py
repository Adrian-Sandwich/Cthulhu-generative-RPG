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


# --- playtest telemetry ------------------------------------------------------
# These counters exist to answer one question the LAN playtest could not: when a
# mechanic goes unused, is it unreachable or just unsignposted? Each test below
# reproduces one of the two real sessions that made the question unanswerable.

def test_telemetry_starts_empty(engine):
    t = engine.telemetry_summary()
    assert t["actions"] == 0 and t["rolls_offered"] == 0
    assert t["mechanic_silent"] is False      # too early to conclude anything
    assert t["dice_undiscovered"] is False
    assert t["dm_roll_compliance"] is None    # no division by zero


def test_telemetry_counts_actions_and_synthesized_rolls(engine):
    from unittest.mock import patch
    # The DM narrates without ever tagging a roll, so the engine's keyword
    # fallback has to inject one — the case where the model ignores the protocol.
    with patch.object(engine, "_call_ollama", return_value="The stairs groan under you."):
        engine.process_player_action("trepo por las escaleras")

    t = engine.telemetry_summary()
    assert t["actions"] == 1
    assert t["rolls_synthesized"] == 1
    assert t["rolls_from_dm"] == 0
    assert t["dm_roll_compliance"] == 0.0     # the engine carried it, not the DM


def test_telemetry_counts_dm_requested_rolls(engine):
    from unittest.mock import patch
    dm = "Something shifts in the dark. [ROLL: spot hidden/Normal]"
    with patch.object(engine, "_call_ollama", return_value=dm):
        engine.process_player_action("look into the corner")

    t = engine.telemetry_summary()
    assert t["rolls_from_dm"] == 1
    assert t["rolls_synthesized"] == 0
    assert t["dm_roll_compliance"] == 1.0


def test_telemetry_counts_thrown_dice(engine):
    from unittest.mock import patch
    dm = "Something shifts in the dark. [ROLL: spot hidden/Normal]"
    with patch.object(engine, "_call_ollama", return_value=dm):
        engine.process_player_action("look into the corner")
        engine.execute_skill_check("spot hidden", "Normal")
        engine.resolve_roll_consequences()

    assert engine.telemetry_summary()["rolls_thrown"] == 1


def test_telemetry_flags_silent_mechanic(engine):
    """angelin's session: 29 actions, 0 rolls — Spanish verbs never matched."""
    from unittest.mock import patch
    with patch.object(engine, "_call_ollama", return_value="The fog rolls past."):
        for _ in range(6):
            # Deliberately a verb with no entry in ROLL_KEYWORDS.
            engine.process_player_action("contemplo el horizonte")

    t = engine.telemetry_summary()
    assert t["actions"] >= 5
    assert t["rolls_offered"] == 0
    assert t["mechanic_silent"] is True
    assert t["dice_undiscovered"] is False    # no dice were ever offered


def test_telemetry_flags_undiscovered_dice(engine):
    """Champi's session: dice offered, never thrown — he typed 'Lanza el dado'."""
    from unittest.mock import patch
    dm = "Something shifts in the dark. [ROLL: spot hidden/Normal]"
    with patch.object(engine, "_call_ollama", return_value=dm):
        for _ in range(2):
            engine.process_player_action("look into the corner")
            engine.state.last_roll = None     # the player never threw it

    t = engine.telemetry_summary()
    assert t["rolls_offered"] >= 2
    assert t["rolls_thrown"] == 0
    assert t["dice_undiscovered"] is True
    assert t["mechanic_silent"] is False      # the mechanic fired fine


def test_telemetry_derives_state_rather_than_counting_it(engine):
    """Derived values must track the state, not a counter that can drift."""
    engine.pick_up_item("revolver")
    t = engine.telemetry_summary()
    assert t["has_firearm"] is True
    assert t["items_held"] == len(engine.state.investigator.inventory)
    assert t["npcs_met"] == len(engine.state.npcs_talked_to)


def test_telemetry_survives_save_and_load(engine, tmp_path):
    engine._track("actions", 7)
    engine._track("rolls_thrown", 2)
    engine.save_game()

    loaded = GenerativeGameEngine.load_game(engine.session_id)
    t = loaded.telemetry_summary()
    assert t["actions"] == 7 and t["rolls_thrown"] == 2


def test_telemetry_never_breaks_a_turn(engine):
    """A broken counter must cost a number, never the turn."""
    engine.state.telemetry = None             # corrupted / absent
    engine._track("actions")                  # must not raise
    assert engine.state.telemetry == {"actions": 1}

    engine.state = None
    engine._track("actions")                  # still must not raise


# --- item pickup fallback ----------------------------------------------------
# Measured against real turns, the local models emit no mechanic tags and return
# no tool calls, so [ITEM_FOUND: key] never fires. Rolls, combat, sanity and
# movement all survive that because they have keyword fallbacks; items had none,
# which is why the LAN playtest recorded "0 armas encontradas" with an AMMO
# counter nobody could spend. These tests pin the fallback and its guards.

def _in_quarters(engine):
    engine.state.location = "Keeper's Quarters"
    return engine


def test_item_pickup_requires_taking_intent(engine):
    _in_quarters(engine)
    # Naming the revolver is not taking it.
    assert engine._infer_item_pickup("miro el revólver sobre la mesa") is None
    assert engine._infer_item_pickup("there is a revolver in the holster") is None
    assert engine._infer_item_pickup("agarro el revólver") == "revolver"
    assert engine._infer_item_pickup("I take the revolver") == "revolver"


def test_item_pickup_is_bilingual(engine):
    _in_quarters(engine)
    for phrase in ("agarro la pistola", "tomo el arma", "recojo el revólver",
                   "I grab the gun", "I pick up the firearm"):
        assert engine._infer_item_pickup(phrase) == "revolver", phrase


def test_item_pickup_respects_placement(engine):
    """A placed item exists in one room; reaching for it elsewhere gets nothing."""
    engine.state.location = "Lighthouse Interior"
    assert engine._infer_item_pickup("agarro el revólver") is None
    _in_quarters(engine)
    assert engine._infer_item_pickup("agarro el revólver") == "revolver"


def test_item_pickup_ignores_unplaced_item_location(engine):
    """Items the adventure does not place can be taken wherever they are found."""
    engine.state.location = "Lighthouse Interior"
    assert engine._infer_item_pickup("recojo la cuerda") == "rope"


def test_item_pickup_will_not_regrant(engine):
    _in_quarters(engine)
    engine.pick_up_item("revolver")
    assert engine._infer_item_pickup("agarro el revólver") is None


def test_item_pickup_rejects_unregistered_items(engine):
    """Pao asked for a knife the adventure has no item for — that must stay a no."""
    _in_quarters(engine)
    assert engine._infer_item_pickup("agarro un cuchillo de la mesa") is None
    assert engine._infer_item_pickup("I take the shotgun") is None


def test_item_pickup_end_to_end_loads_the_firearm(engine):
    """The whole point: AMMO stops being a number the player can never spend."""
    from unittest.mock import patch
    _in_quarters(engine)
    assert engine.resources_status()["has_firearm"] is False

    # A DM that emits no tags at all — which is what the real models do.
    with patch.object(engine, "_call_ollama",
                      return_value="You rummage through the keeper's effects."):
        result = engine.process_player_action("registro los efectos y agarro el revólver")
    engine.apply_turn_consequences(result)

    assert "Revolver (.38)" in engine.state.investigator.inventory
    assert engine.state.ammo == 6
    assert engine.resources_status()["has_firearm"] is True
    assert engine.telemetry_summary().get("items_synthesized") == 1


def test_dm_tag_still_wins_over_the_fallback(engine):
    """The fallback is a backstop; a DM that does tag items keeps control."""
    from unittest.mock import patch
    _in_quarters(engine)
    dm = "A coil of rope hangs by the door. [ITEM_FOUND: rope]"
    with patch.object(engine, "_call_ollama", return_value=dm):
        result = engine.process_player_action("miro alrededor")
    engine.apply_turn_consequences(result)

    assert "Rope (30ft)" in engine.state.investigator.inventory
    # Tagged, not synthesized — the counter must tell them apart.
    assert engine.telemetry_summary().get("items_synthesized", 0) == 0


# --- prompt composed by measured capability ----------------------------------
# Telemetry over real turns showed the local models emitting zero mechanic tags,
# so for them the tag directives were tokens spent every turn asking for a format
# that never arrived. They now ship only to models measured as able to emit them.
# What must NOT be conditional is the behaviour that closed playtest findings:
# world containment and the anti-dream-reset rule.

import re as _re

TAG_DIRECTIVE = _re.compile(r"\[[A-Z_]+:")


def _prompt_for(model, tmp_path):
    os.environ["DATA_DIR"] = str(tmp_path)
    e = GenerativeGameEngine(model=model, use_memory=False,
                             use_entity_graph=False, session_id=f"p{abs(hash(model))}")
    e.create_game(create_investigator("T", "scholar"))
    return e._build_dm_system_prompt()


def test_tagless_model_gets_no_tag_directives(tmp_path):
    prompt = _prompt_for("mistral", tmp_path)
    leftovers = [l for l in prompt.splitlines() if TAG_DIRECTIVE.search(l)]
    assert leftovers == [], leftovers


def test_tag_capable_model_still_gets_the_protocol(tmp_path):
    from core.cthulhu_tools import TOOL_CAPABLE_MODELS
    model = sorted(TOOL_CAPABLE_MODELS)[0]
    prompt = _prompt_for(model, tmp_path)
    assert TAG_DIRECTIVE.search(prompt), "a capable model lost its tag protocol"
    for tag in ("[ROLL:", "[ITEM_FOUND:", "[COMBAT_START:", "[LOCATION:"):
        assert tag in prompt, tag


def test_containment_rules_ship_to_every_model(tmp_path):
    """These closed playtest findings #2 and #3 — they are not optional."""
    for model in ("mistral", "qwen2.5:7b"):
        # Collapse wrapping: the prompt hard-wraps mid-sentence.
        low = " ".join(_prompt_for(model, tmp_path).lower().split())
        assert "do not invent" in low, model          # world containment
        assert "cannot rewrite reality" in low, model  # anti-dream-reset
        assert "dream" in low, model
        assert "stat blocks" in low, model


def test_dropping_tags_shrinks_the_prompt(tmp_path):
    tagless = _prompt_for("mistral", tmp_path)
    tagged = _prompt_for("qwen2.5:7b", tmp_path)
    assert len(tagless) < len(tagged)


def test_unmatched_action_is_counted(engine):
    """A turn with no check is a gap in ROLL_KEYWORDS, not a quiet non-event."""
    from unittest.mock import patch
    with patch.object(engine, "_call_ollama", return_value="The fog drifts past."):
        engine.process_player_action("contemplo el horizonte en silencio")
    assert engine.telemetry_summary()["actions_without_check"] == 1

    with patch.object(engine, "_call_ollama", return_value="You haul yourself up."):
        engine.process_player_action("trepo por la escalera")
    # A matched action must not be counted as a gap.
    assert engine.telemetry_summary()["actions_without_check"] == 1
