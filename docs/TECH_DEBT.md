# Technical Debt

Known, deliberately-deferred items. None block launch; listed so they're not
forgotten.

## God object: `GenerativeGameEngine` (core/game_generative.py, 1924 lines)
Mixes CoC rules, prompt building, combat, NPCs, sanity, resources, saves, i18n,
and playtest export in one class. It works and is covered by the smoke suite,
but it's the main friction point for future changes.

**Proposed split** (post-launch, behind the test suite as a safety net):
- `PromptBuilder` — system/DM/consequence prompt assembly + language directives.
- `CombatSystem` — start/round/flee/enemy inference.
- `NPCSystem` — encounters, reputation, companions, dossier.
- keep `GenerativeGameEngine` as the thin orchestrator.

Deferred because a large refactor right before a public launch is high-risk for
low user-visible gain. Do it when a feature actually needs it.

## Manual playtest scripts

The manual generative playtests live under `tools/` and are intentionally not
collected by the automated test suite. Run them from the repository root:

```bash
python tools/test_gameplay.py
python tools/test_generative_flow.py
python tools/test_generative_with_selection.py
```

The first two scripts exercise the generative engine and may require a
configured LLM. The selection playtest needs an interactive TTY; omit `-q` to
see its prompts.

## Partially wired `location_state` features
`reveal_secret` is wired (MAGI #37): a **successful discovery roll** (Spot
Hidden, Library Use, Occult… — `DISCOVERY_SKILLS` in
`core/keyword_data.py`) makes the engine record an engine-generated secret on
the current location, which stops that location's danger escalation and puts
the names of the last finds into the DM prompt. It is deliberately not driven
by an LLM tag: the local models were measured emitting zero tags
(`docs/PLAYTEST_FINDINGS.md`), so a tag-only mechanic would be invisible.
Covered in `tests/test_engine_units.py` (idempotence, garbage keys, 8-per-
location cap, save/load with and without the fields).

Before this wiring nothing ever populated `secrets_revealed`, so
`visit_location` pushed `danger_level` to 5/5 on every revisited location in
every game and told the Keeper so. **Saves written before it** load fine
(missing lists default to empty) but keep whatever danger level they had
reached; it stops climbing only once a secret is found there.

Decided in MAGI #39 (2026-09-17):

- `SECRET_UNLOCKS` / `DANGER_REDUCING_SECRETS` were **deleted**. They were
  keys of one adventure that would silently never match in
  dark/tide/point_black; generalizing them through `AdventureConfig` was
  discarded because no adventure asks for it. Recoverable from git if one does.
- `listen` and `science` were **removed from `DISCOVERY_SKILLS`**: a secret
  freezes the location's danger escalation for good, and a Listen the DM asked
  for because something made a noise is not a search of the place. Melchior's
  dissent is recorded: in CoC a successful Listen does reveal the hidden thing;
  revisit if playtests show players expecting it.
- `trigger_event` **stays without a caller**, deliberately. Wiring it to combat
  start (the one caller proposed) would write engine-generated event slugs
  into every later prompt with no adventure-level meaning behind them. It is
  hardened and tested; it gets a caller when an adventure defines events.

Contamination is wired (MAGI #40): every SAN point lost stains the current
location (`CONTAMINATION_PER_SAN`) and every turn past the doom clock adds
`CONTAMINATION_PER_DOOM_TURN` on top, both engine-owned in
`core/game_generative.py` (`_stain_location`). The level reaches the DM as
prose by tier (`describe_contamination`), the player through the location
description, and the image pipeline snapped to its tier
(`contamination_bucket`) so the cache does not regenerate per SAN point.
`increase/decrease_contamination` resolve by key or display name; the direct
dict lookup they had was a silent no-op for the engine, which tracks the
location by name.

Discarded in #40, on the record:

- **Lowering `danger_level` by 1 on a found secret.** `danger_level` has no
  mechanical consumer (only narration, DM context and its own escalation), so
  the change would have edited prose and nothing else.
- **Deleting contamination.** `game/game_image_integration.py` and
  `game/art_director.py` read it; deleting would break a working subsystem.
- **A caller for `decrease_contamination`.** Resting does not cleanse a room;
  it waits for an adventure that defines a sealing rite.
- **The discarded return value of `visit_location`** (its threshold prose
  never reaches the player). Changes what the player sees; its own decision.

## Local-only content moderation
`core/moderation.py` ships a conservative local blocklist by default. An
OpenAI-compatible `/moderations` API path exists (`MODERATION=api`) but adds
per-turn latency/cost and isn't enabled. Turn it on before a truly open,
unmonitored public launch.

## Single-process session registry
The in-memory `_sessions` map + per-session locks require gunicorn to run with
ONE worker (documented in the Dockerfile/DEPLOY). Horizontal scaling would need
the session/game state moved to a shared store (Redis/DB). Fine for the current
scale; revisit if one process isn't enough.

## Dead standalone scripts (fan-in 0 in the code graph)
`game/generate_examples.py`, `game/generate_final_test.py`,
`game/show_all_images.py`, `game/debug_generation.py`,
`game/evaluate_examples.py`, `tools/analyze_playtests.py`, and
`tools/document_to_json.py` are one-off CLI/experiment scripts nothing in the
app imports. Kept on purpose (image-gen experiments and data tooling), but they
are not part of the runtime and are excluded from launch review scope. Delete
whenever the image-generation experiments conclude.
