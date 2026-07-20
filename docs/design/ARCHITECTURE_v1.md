# Cthulhu Engine v1 - Architecture

Clean, modular game engine for Call of Cthulhu 7e generative adventures.

## Directory Structure

```
cthulhu_engine/                          # Main engine package
├── __init__.py                          # Package exports
├── engine.py                            # Main orchestrator
├── state.py                             # Game state & rules (CoC7eRulesEngine)
│
├── core/
│   ├── __init__.py
│   ├── systems/                         # Game mechanics
│   │   ├── sanity.py                    # Sanity checks, disorders, breaking points
│   │   ├── companions.py                # Companion relationship mechanics
│   │   ├── location.py                  # Location state & secrets
│   │   └── ending.py                    # Ending types & narratives
│   │
│   ├── memory/                          # Persistence & memory
│   │   ├── dm_memory.py                 # Semantic memory (ChromaDB + mem0ai)
│   │   ├── entity_graph.py              # NPC relationships (Neo4j)
│   │   └── generative_save.py           # Save/load system
│   │
│   └── llm/ (FUTURE)                    # LLM integration
│       ├── dm_prompt.py                 # DM system prompt building
│       ├── tool_calling.py              # Tool definitions & execution
│       └── ollama_client.py             # Ollama API wrapper
│
├── ui/
│   ├── __init__.py
│   ├── terminal/                        # Terminal display (CLI)
│   │   ├── colors.py                    # ANSI color system
│   │   ├── thinking.py                  # Keeper thinking animation
│   │   ├── history.py                   # History viewer/pager
│   │   └── display.py (FUTURE)          # Main terminal display
│   │
│   └── graphics/ (FUTURE - PLUG & PLAY) # Graphical layer
│       ├── snapshot_manager.py          # Game snapshots (images + state)
│       ├── image_generator.py           # Procedural/AI image generation
│       └── display.py                   # Graphics display
│
├── data/
│   ├── __init__.py
│   ├── adventure_context.py             # Adventure data & templates
│   ├── tools.py                         # LLM tool definitions
│   ├── npcs.json (FUTURE)               # NPC definitions
│   └── locations.json (FUTURE)          # Location templates
│
└── utils/
    ├── __init__.py
    ├── config.py                        # Configuration
    └── logging.py                       # Logging utilities

games/
├── play_terminal.py                     # ✅ Main entry point (CLI)
└── play_graphical.py (FUTURE)           # Graphical entry point

adventures/
├── point_black/                         # Point Black adventure data
├── tide/                                # Tides of Madness adventure
└── dark/                                # In the Dark adventure
```

## Key Components

### Engine (engine.py)
```python
engine = CthulhuEngine(
    adventure_name="point_black",
    investigator_name="Dr. Smith",
    model="mistral",
    use_memory=True,
    use_neo4j=False
)

state = engine.create_game(stats)
result = engine.process_turn("I examine the door")
engine.execute_skill_check("investigate", "Normal")
engine.save_game()
```

### Game State (state.py)
- `GameState` - Complete game session state
- `InvestigatorState` - Player character
- `CoC7eRulesEngine` - Rules enforcement (d100, difficulty mods, etc.)

### Systems (core/systems/)
Each system is independent and can be tested separately:
- `SanitySystem` - Sanity damage, breaking points, mental disorders
- `CompanionSystem` - Multi-companion tracking & relationships
- `LocationState` - Dynamic location state, secrets, danger levels
- `EndingSystem` - 8 ending types + epilogues

### Memory (core/memory/)
- `DMMemory` - Semantic memory with fact extraction (ChromaDB + mem0ai)
- `EntityGraph` - NPC relationships & conspiracy detection (Neo4j)
- `GameSaveManager` - Automatic save/load with full state persistence

### UI Layers (ui/)
- **Terminal** (current): ANSI colors, animations, interactive pager
- **Graphics** (future): Snapshot-based with image generation

## Adding the Graphics Layer

The graphics layer is **plug-and-play**:

```python
# Terminal version (current)
from cthulhu_engine.ui.terminal import TerminalDisplay
display = TerminalDisplay()

# Graphics version (future)
from cthulhu_engine.ui.graphics import GraphicsDisplay
display = GraphicsDisplay()

# Same engine works with either!
engine = CthulhuEngine(...)
result = engine.process_turn(action)
display.show_result(result)
```

## Initialization Sequence

```
1. CthulhuEngine created
   ├── Initialize all systems
   ├── Initialize memory (DMMemory, EntityGraph)
   └── Create SaveManager
   
2. create_game(stats)
   ├── Create InvestigatorState
   └── Create GameState
   
3. Main loop
   ├── process_turn(action)
   │   ├── LLM narration (future: move to llm/)
   │   ├── Skill checks if needed
   │   ├── Update systems (sanity, companions, ending)
   │   └── Save state
   └── Display result via UI
```

## Testing

Each system can be tested independently:

```python
from cthulhu_engine.core.systems import SanitySystem
from cthulhu_engine.state import InvestigatorState

sanity_sys = SanitySystem()
inv = InvestigatorState(...)
result = sanity_sys.apply_damage(inv, 5, "witnessed horror")
```

## Migration Notes (v0 → v1)

- Old `core/game_generative.py` is now split into modular pieces
- Old UI components moved to `ui/terminal/`
- Old play scripts consolidated into `games/play_terminal.py`
- Dead code archived in `archive/`
- All imports updated to use new paths

## What's Next

**Phase 2**: Implement graphics layer
- Snapshot manager
- Procedural image generation
- Graphics display UI
- Plug into existing engine

**Phase 3**: Performance & content
- Optimize LLM calls
- Add more adventures
- Expand NPC/location database
