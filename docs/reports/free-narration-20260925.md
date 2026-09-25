# Free narration verification — 2026-09-25

## Changes

- Supply current location, its description, inventory, ammunition and last roll as server facts.
- Request brief sensory narration without assigning player thoughts or granting discoveries.
- Reject known completed moves to other locations and pickups of uncarried authored items before streaming or tool execution.
- Remove contradictory prompt guidance about eight possible endings and model-authored transitions.
- Fix local Ollama chat requests: system instructions belong in `messages` with role `system`. The old top-level `system` field was inappropriate for `/api/chat`; see the [Ollama chat API](https://docs.ollama.com/api/chat).

## Verification

The full local suite passed: **325 tests**, including real PostgreSQL integration and Node frontend checks. Pyright reported zero errors and two existing warnings in `core/entity_graph.py`.

Regressions cover false movement and pickup claims in English and Spanish, legitimate mentions and conditional attempts, current inventory, buffered SSE rejection with state rollback, tool-response validation, and system messages reaching both chat providers.

Two real local requests used `qwen2.5:3b`. Before the transport fix, listening to the wind produced generic assistant advice about wind, and examining the walls produced advice about meditation. After the fix:

| Action | Observed response |
| --- | --- |
| `I listen to the wind outside.` | Salt wind, faint whispers and a metallic scent; the narrator asks what the investigator will do next. |
| `I examine the lighthouse walls without moving.` | Describes faint maritime decoration beneath weathering and leaves an unanswered question. |

Both responses passed the output checks. The first request encountered a timeout and succeeded on retry. These two samples verify the repaired instruction delivery and basic scene continuity; they are not a broad narrative-quality evaluation. The model still improvises descriptive details, and pattern checks cannot detect every invented fact or paraphrase.

This verification is local. The earlier [production release report](release-readiness-20260925/README.md) describes the previously deployed image; it does not establish deployment of these later narration changes.
