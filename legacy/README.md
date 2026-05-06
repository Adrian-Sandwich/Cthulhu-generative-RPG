# Legacy Code Archive

This folder contains obsolete code kept for historical reference and potential recovery.

## Contents

### `core/`
- **game_universal.py** — First iteration of game motor (JSON-based, no LLM)
- **game_enhanced.py** — Second iteration (added save/load system)
- **game_immersive.py** — Third iteration (added ASCII art interface)

All replaced by **game_generative.py** (current production engine with LLM integration via Ollama).

### `games/`
- **play.py**, **play_fixed.py**, **play_improved.py** — Early CLI prototypes
- **play_immersive.py** — Used old game_immersive engine
- **play_terminal.py** — Experimental terminal engine
- **quick_play.py** — Quick test variant

All replaced by **play_generative.py** (current production CLI).

### `ui/`
- **demo_retro_ui.py** — Standalone demo of retro terminal UI (old)

Active UI modules remain in `ui/`: color_system.py, keeper_thinking.py, history_viewer.py, etc.

### `graphics_engine/`
- **main.py** — Standalone demo of procedural image generator
- **batch_generator.py** — Test batch image generation script
- **generate_variations.py** — Image variation generator
- **refine_batch.py** — Batch refinement utility
- **data/test_snapshots/** — Empty test directory
- **data/templates/** — Empty template directory

Active graphics modules remain in `graphics_engine/`: ascii_scenes_hd.py, snapshot.py, storage.py.

## Why Keep It?

- **Reference**: Understanding evolution of the game engine
- **Recovery**: Can reference old patterns if needed
- **History**: Complete development record

## To Use Legacy Code

If you need to run an old script:
```bash
cd legacy
python games/play_immersive.py
# (will fail unless you restore old core modules)
```

**Note**: Legacy code is not maintained and may have import/dependency issues.

---

**Archived**: May 6, 2026
**Size**: Minimal (~200KB combined)
**Status**: Do not modify or extend
