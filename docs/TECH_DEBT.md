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

## Unused rich `location_state` features
`reveal_secret`, `trigger_event`, contamination mechanics exist and are tested
but never wired into gameplay. Decision pending: wire them (the world reacts —
secrets found via Spot Hidden, contamination rising with the doom clock) or
delete them. Leaving dead-but-tested code is the current (acceptable) state.

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
