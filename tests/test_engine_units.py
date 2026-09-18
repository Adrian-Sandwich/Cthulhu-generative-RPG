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


@pytest.fixture(autouse=True)
def _reset_llm_degradation():
    """The degraded-turn counter is process-wide by design (it answers "is the
    model answering at all", not a per-session question), which makes tests
    order-dependent unless it is reset."""
    from core.llm_client import LLMClient
    LLMClient.degraded_turns = 0
    LLMClient.last_error = None
    yield
    LLMClient.degraded_turns = 0
    LLMClient.last_error = None


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


# --- LLM transport: reasoning budget and loud degradation --------------------
# Production ran for weeks on a model the provider had retired. Every turn
# 404'd, the engine swallowed it and served a canned sentence, and /api/health
# still said "ok" because it never calls the model. Two guards come from that.

def test_reasoning_models_get_a_low_effort_hint():
    """A reasoning model spends the completion budget thinking before it writes.

    Measured on Groq with gpt-oss-120b and this game's ~2000-token system
    prompt: at the engine's 150-token cap it produced 664 characters of
    reasoning and ZERO characters of narration, so every turn degraded to the
    fallback. Asking for low effort returns the same narration in 48 tokens
    instead of 281.
    """
    from core.llm_client import LLMClient

    def opts(model):
        return LLMClient(model=model, provider="openai",
                         endpoint="http://x", api_key="k")._reasoning_options()

    for model in ("openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"):
        assert opts(model) == {"reasoning_effort": "low"}, model

    # Non-reasoning models must not receive the field: providers reject
    # unknown parameters outright.
    for model in ("mistral", "llama-3.3-70b-versatile"):
        assert opts(model) == {}, model


def test_degraded_turns_are_counted_not_swallowed():
    """A fallback must leave a trace, or a dead config looks like normal play."""
    from core.llm_client import LLMClient

    before = LLMClient.degraded_turns
    out = LLMClient._degrade("model_not_found", LLMClient.GENERIC_FALLBACK)

    assert out == LLMClient.GENERIC_FALLBACK       # the turn stays playable
    assert LLMClient.degraded_turns == before + 1  # but it is visible
    assert LLMClient.last_error == "model_not_found"


def test_tool_capable_models_are_the_measured_ones():
    """This set is measured, not assumed — it was inverted once already."""
    from core.cthulhu_tools import TOOL_CAPABLE_MODELS

    # Returned pickup_item for an unambiguous "take the revolver".
    assert "openai/gpt-oss-120b" in TOOL_CAPABLE_MODELS
    assert "qwen2.5:7b" in TOOL_CAPABLE_MODELS
    # Returned zero tool calls and narrated it in prose instead.
    for model in ("mistral", "neural-chat", "llama3"):
        assert model not in TOOL_CAPABLE_MODELS, model


# --- location secrets: a successful discovery roll leaves a mark -------------
# MAGI decision #37: the ENGINE records the find (never an LLM tag, measured at
# zero emission), the location stops escalating in danger, and the DM sees the
# names of what was uncovered in every later prompt.

def _roll(skill, success=True):
    return {"skill": skill, "difficulty": "Normal", "success": success,
            "roll": 5 if success else 95, "target": 50, "message": ""}


def test_successful_discovery_roll_records_a_secret_on_the_location(engine):
    from unittest.mock import patch
    engine.state.last_roll = _roll("spot hidden")
    with patch.object(engine, "_call_ollama", return_value="You notice scratches on the floor."):
        out = engine.resolve_roll_consequences()

    loc = engine.location_state.get_location(engine.state.location)
    assert loc is not None
    assert loc.secrets_revealed == [f"spot_hidden_turn_{engine.state.turn}"]
    # The UI shows the bite of a roll through `consequence.label`.
    assert out["consequence"]["kind"] == "secret"
    assert out["consequence"]["label"] == "SECRET FOUND"
    assert out["hp_damage"] == [] and out["sanity_checks"] == []
    assert engine.telemetry_summary().get("secrets_revealed", 0) == 1 or \
        engine.state.telemetry["secrets_revealed"] == 1


def test_discovery_reaches_the_dm_prompt_by_name(engine):
    from unittest.mock import patch
    engine.state.last_roll = _roll("library use")
    with patch.object(engine, "_call_ollama", return_value="A ledger, hidden."):
        engine.resolve_roll_consequences()

    ctx = engine._get_location_context_for_prompt()
    # Prose, not the stored slug: a weak model narrates "library_use_turn_1"
    # as if it were an object (MAGI #38, casper's condition).
    assert "a hidden detail uncovered with library use on turn" in ctx
    assert "library_use" not in ctx and "library use turn" not in ctx
    assert "1 secret(s) found here" in ctx


def test_non_discovery_and_failed_rolls_record_nothing(engine):
    from unittest.mock import patch
    loc = engine.location_state.get_location(engine.state.location)
    with patch.object(engine, "_call_ollama", return_value="Narration."):
        engine.state.last_roll = _roll("climb")                 # success, not discovery
        out = engine.resolve_roll_consequences()
        assert out["consequence"] is None
        engine.state.last_roll = _roll("spot hidden", success=False)
        out = engine.resolve_roll_consequences()
        assert out["consequence"]["kind"] == "san"              # the failure path is untouched
    assert loc.secrets_revealed == []


def test_discovery_is_idempotent_within_a_turn(engine):
    from unittest.mock import patch
    with patch.object(engine, "_call_ollama", return_value="Narration."):
        engine.state.last_roll = _roll("spot hidden")
        first = engine.resolve_roll_consequences()
        engine.state.last_roll = _roll("spot hidden")
        second = engine.resolve_roll_consequences()
    loc = engine.location_state.get_location(engine.state.location)
    assert len(loc.secrets_revealed) == 1
    assert first["consequence"] is not None and second["consequence"] is None


def test_secret_stops_the_danger_escalation():
    """The live bug: nothing ever populated secrets_revealed, so every revisit
    pushed danger to 5/5 in every game and the Keeper was told so."""
    from core.location_state import LocationStateManager
    haunted = LocationStateManager()
    haunted.register_location("hall", "Great Hall", "")
    for turn in range(1, 8):
        haunted.visit_location("Great Hall", turn)
    assert haunted.get_location("hall").danger_level == 5   # untouched location: escalates

    known = LocationStateManager()
    known.register_location("hall", "Great Hall", "")
    known.visit_location("Great Hall", 1)
    known.visit_location("Great Hall", 2)
    assert known.get_location("hall").danger_level == 2
    assert known.reveal_secret("Great Hall", "spot_hidden_turn_2")["success"]
    for turn in range(3, 10):
        known.visit_location("Great Hall", turn)
    assert known.get_location("hall").danger_level == 2      # frozen once something was found


def test_reveal_secret_resolves_by_display_name_and_by_key():
    from core.location_state import LocationStateManager
    mgr = LocationStateManager()
    mgr.register_location("lighthouse_exterior", "Point Black Lighthouse - Exterior", "")
    assert mgr.reveal_secret("Point Black Lighthouse - Exterior", "a")["success"]
    assert mgr.reveal_secret("lighthouse_exterior", "b")["success"]
    assert mgr.get_location("lighthouse_exterior").secrets_revealed == ["a", "b"]
    assert mgr.reveal_secret("Nowhere", "c") == {"success": False, "reason": "unknown_location"}


def test_reveal_secret_rejects_garbage_and_duplicates_without_mutating():
    from core.location_state import LocationStateManager
    mgr = LocationStateManager()
    mgr.register_location("hall", "Great Hall", "")
    for bad in ("", "   ", "!!!", "x" * 41, None, 42):
        res = mgr.reveal_secret("hall", bad)
        assert res["success"] is False and res["reason"] == "invalid_key"
    assert mgr.reveal_secret("hall", "Keeper's Diary")["success"]      # slugified
    assert mgr.get_location("hall").secrets_revealed == ["keeper_s_diary"]
    dup = mgr.reveal_secret("hall", "keeper_s_diary")
    assert dup["success"] is False and dup["reason"] == "already_revealed"
    assert mgr.get_location("hall").secrets_revealed == ["keeper_s_diary"]


def test_reveal_secret_caps_at_eight_per_location():
    from core.location_state import LocationStateManager
    mgr = LocationStateManager()
    mgr.register_location("hall", "Great Hall", "")
    for i in range(8):
        assert mgr.reveal_secret("hall", f"s{i}")["success"]
    ninth = mgr.reveal_secret("hall", "s8")
    assert ninth["success"] is False and ninth["reason"] == "cap_reached"
    assert len(mgr.get_location("hall").secrets_revealed) == 8
    # The context names only the most recent ones and keeps the total.
    ctx = mgr.get_location_context("hall")
    assert "8 secret(s) found here: s5; s6; s7" in ctx


def test_single_adventure_secret_tables_are_gone():
    """SECRET_UNLOCKS / DANGER_REDUCING_SECRETS were keys of one adventure that
    would silently never match elsewhere; MAGI #39 deleted them rather than
    generalizing them. A secret with one of their old keys is just a secret."""
    from core.location_state import LocationStateManager
    assert not hasattr(LocationStateManager, "SECRET_UNLOCKS")
    assert not hasattr(LocationStateManager, "DANGER_REDUCING_SECRETS")
    mgr = LocationStateManager()
    mgr.register_location("hall", "Great Hall", "")
    mgr.get_location("hall").danger_level = 4
    res = mgr.reveal_secret("hall", "hidden_passage")
    assert res["success"] and "unlocked_location" not in res
    assert mgr.unlocked_locations == {"hall"}
    mgr.reveal_secret("hall", "ritual_seal")
    assert mgr.get_location("hall").danger_level == 4


def test_listen_and_science_successes_do_not_freeze_the_danger(engine):
    """A Listen the DM asked for because something made a noise is not a
    search of the place: it must not leave a secret, so the location keeps
    escalating. Spot Hidden still records (MAGI #39)."""
    from unittest.mock import patch
    loc = engine.location_state.get_location(engine.state.location)
    with patch.object(engine, "_call_ollama", return_value="Narration."):
        for skill in ("listen", "Listen", "science"):
            engine.state.last_roll = _roll(skill)
            out = engine.resolve_roll_consequences()
            assert out["consequence"] is None
    assert loc.secrets_revealed == []
    before = loc.danger_level
    engine.location_state.visit_location(engine.state.location, engine.state.turn + 1)
    assert loc.danger_level == before + 1                  # still escalating

    with patch.object(engine, "_call_ollama", return_value="Narration."):
        engine.state.last_roll = _roll("spot hidden")
        assert engine.resolve_roll_consequences()["consequence"]["kind"] == "secret"
    engine.location_state.visit_location(engine.state.location, engine.state.turn + 2)
    assert loc.danger_level == before + 1                  # frozen by the real find


def test_trigger_event_resolves_by_name_and_is_idempotent():
    from core.location_state import LocationStateManager
    mgr = LocationStateManager()
    mgr.register_location("hall", "Great Hall", "")
    assert mgr.trigger_event("Great Hall", "Lights Out") is True
    assert mgr.trigger_event("hall", "lights_out") is False
    assert mgr.trigger_event("hall", "???") is False
    assert mgr.trigger_event("Nowhere", "x") is False
    assert mgr.get_location("hall").events_triggered == ["lights_out"]
    assert "events that happened here: lights out" in mgr.get_location_context("hall")


def test_location_secrets_round_trip_through_save_and_load(engine):
    from unittest.mock import patch
    engine.state.last_roll = _roll("spot hidden")
    with patch.object(engine, "_call_ollama", return_value="Narration."):
        engine.resolve_roll_consequences()
    engine.save_game()

    loaded = GenerativeGameEngine.load_game(engine.session_id)
    loc = loaded.location_state.get_location(loaded.state.location)
    assert loc.secrets_revealed == [f"spot_hidden_turn_{engine.state.turn}"]
    # And it keeps its danger frozen after the load too.
    before = loc.danger_level
    loaded.location_state.visit_location(loaded.state.location, 99)
    assert loc.danger_level == before


def test_location_state_loads_a_save_without_the_secret_fields():
    """Saves written before this wiring have no secrets/events lists."""
    from core.location_state import LocationStateManager
    old_save = {
        "locations": {
            "hall": {"key": "hall", "name": "Great Hall", "base_description": "",
                     "visited_count": 3, "danger_level": 3},
        },
        "unlocked": ["hall"],
    }
    mgr = LocationStateManager.from_dict(old_save)
    loc = mgr.get_location("Great Hall")
    assert loc.secrets_revealed == [] and loc.events_triggered == []
    assert mgr.reveal_secret("Great Hall", "found_it")["success"]
    again = LocationStateManager.from_dict(mgr.to_dict())
    assert again.get_location("hall").secrets_revealed == ["found_it"]


def test_failure_consequence_matches_spaced_skill_names(engine):
    """'spot hidden' (as the DM and the UI spell it) must hit the mental pool,
    not fall through to a generic setback; 'library use' and 'climb' likewise."""
    san = engine._failure_consequence(_roll("spot hidden", success=False))
    assert san["kind"] == "san" and san["amount"] >= 1
    lib = engine._failure_consequence(_roll("Library Use", success=False))
    assert lib["kind"] == "san"
    hp = engine._failure_consequence(_roll("climb", success=False))
    assert hp["kind"] == "hp"
    social = engine._failure_consequence(_roll("charm", success=False))
    assert social["kind"] == "setback"


# --- contamination: horror leaves a stain on the place -----------------------
# MAGI decision #40: fed by SAN loss and the doom clock (events measured as
# firing in real sessions without dice), never by an LLM tag. Prose by tier in
# the DM context; tier-snapped for the image cache.

def test_contamination_resolves_by_display_name_and_clamps():
    from core.location_state import LocationStateManager
    mgr = LocationStateManager()
    mgr.register_location("lighthouse_exterior", "Point Black Lighthouse - Exterior", "")
    assert mgr.increase_contamination("Point Black Lighthouse - Exterior", 30) == 30
    assert mgr.increase_contamination("lighthouse_exterior", 90) == 100          # clamp
    assert mgr.decrease_contamination("Point Black Lighthouse - Exterior", 40) == 60
    assert mgr.decrease_contamination("lighthouse_exterior", 500) == 0            # floor
    assert mgr.increase_contamination("Nowhere", 10) is None
    assert mgr.increase_contamination("lighthouse_exterior", -5) == 0             # no negative feed
    assert mgr.increase_contamination("lighthouse_exterior", "junk") == 0         # no mutation


def test_contamination_reaches_the_dm_as_prose_not_a_percentage():
    from core.location_state import LocationStateManager
    mgr = LocationStateManager()
    mgr.register_location("hall", "Great Hall", "")
    assert "tainted" not in mgr.get_location_context("hall")
    mgr.increase_contamination("hall", 10)
    ctx = mgr.get_location_context("hall")
    assert "faint wrongness" in ctx and "%" not in ctx
    mgr.increase_contamination("hall", 20)                                        # 30
    ctx = mgr.get_location_context("hall")
    assert "profoundly wrong" in ctx and "%" not in ctx and "30" not in ctx
    mgr.increase_contamination("hall", 50)                                        # 80
    assert "Reality seems to bend" in mgr.get_location_context("hall")
    assert "Reality seems to bend" in mgr.get_location("hall").get_current_description()


def test_contamination_bucket_snaps_to_tiers():
    from core.location_state import contamination_bucket
    assert [contamination_bucket(v) for v in (0, 5, 24, 25, 49, 50, 74, 75, 100)] == \
        [0, 0, 0, 25, 25, 50, 50, 75, 75]


def test_sanity_loss_stains_the_current_location(engine):
    from core.keyword_data import CONTAMINATION_PER_SAN
    loc = engine.location_state.get_location(engine.state.location)
    assert loc.contamination == 0
    engine.apply_sanity_check(5, source="the thing in the water")
    assert loc.contamination == 5 * CONTAMINATION_PER_SAN
    assert engine.telemetry_summary()["contamination_raised"] == 1
    engine.apply_sanity_check(0, source="nothing")                               # no stain
    assert loc.contamination == 5 * CONTAMINATION_PER_SAN
    assert engine.telemetry_summary()["contamination_raised"] == 1


def test_doom_clock_corrupts_the_place_every_overdue_turn(engine):
    from unittest.mock import patch
    from core.keyword_data import CONTAMINATION_PER_SAN, CONTAMINATION_PER_DOOM_TURN
    loc = engine.location_state.get_location(engine.state.location)
    engine.state.time_limit = engine.state.turn                                   # out of time now
    with patch.object(engine, "_call_ollama", return_value="The fog thickens."):
        engine.process_player_action("wait")
    # The overdue turn bleeds 2 SAN (stain) and the presence adds its own.
    assert loc.contamination == 2 * CONTAMINATION_PER_SAN + CONTAMINATION_PER_DOOM_TURN
    assert any("presence draws nearer" in n for n in engine.state.narrative)


def test_stain_is_silent_without_location_state(engine):
    engine.location_state = None
    res = engine.apply_sanity_check(3, source="a test")
    assert "error" not in res                                                     # SAN path untouched
    assert engine._stain_location(10) is None


def test_contamination_survives_save_and_load(engine):
    engine.apply_sanity_check(6, source="the thing in the water")
    before = engine.location_state.get_location(engine.state.location).contamination
    assert before > 0
    engine.save_game()
    loaded = GenerativeGameEngine.load_game(engine.session_id)
    assert loaded.location_state.get_location(loaded.state.location).contamination == before
