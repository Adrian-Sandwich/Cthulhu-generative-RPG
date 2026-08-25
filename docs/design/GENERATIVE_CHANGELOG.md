# Generative Edition - Changelog

## Version 1.0 - April 10, 2026

### ✅ Major Features Implemented

#### Core Engine (`core/game_generative.py`)
- **GenerativeGameEngine**: AI Dungeon Master orchestration
  - Mistral 7B integration via local Ollama
  - Game state management (turns, narrative, stats)
  - Automatic roll/sanity check detection
  - Ending condition evaluation

- **CoC7eRulesEngine**: Call of Cthulhu 7e rules enforcement
  - D100 percentile dice system
  - Difficulty modifiers (Normal/Hard/Extreme)
  - Sanity system with conditional damage
  - Critical success/failure detection (1-5, 96-00)

- **InvestigatorState**: Character data structure
  - Characteristics (STR, CON, DEX, etc.)
  - Skills with normalization (investigate, occult, library, etc.)
  - Inventory system
  - Sanity break tracking

#### Game Interface (`games/play_generative.py`)
- **Character Selection System**
  - Load 4 prebuilt investigators
  - Convert JSON format → InvestigatorState
  - Custom character creation option

- **Interactive Game Loop**
  - Natural language input processing
  - DM response generation
  - Skill check execution
  - Sanity damage application
  - Status display (HP/SAN bars)

- **Commands**
  - `[action text]`: Describe what you do
  - `[i]nventory`: Check items
  - `[s]tatus`: Full character stats
  - `[h]elp`: Show commands
  - `[q]uit`: Save and exit

#### Testing & Demos
- `test_generative_flow.py`: Auto-play 2 turns
- `test_generative_with_selection.py`: Interactive 3-turn test with character selection

### ✅ Preloaded Investigators

**1. Detective Morgan** (Private Investigator)
- HP: 13, SAN: 70, POW: 70
- Strengths: Investigation, Library Use, Persuasion
- Ideal for: Methodical, deductive players

**2. Dr. Elizabeth Chen** (Occult Scholar)
- HP: 10, SAN: 75, POW: 85
- Strengths: Occult knowledge, Languages, Astronomy
- Ideal for: Knowledge-based puzzle solving

**3. Captain James Redford** (Coast Guard Officer)
- HP: 15, SAN: 65, POW: 60
- Strengths: Navigation, Combat, Survival
- Ideal for: Action-oriented, physical challenges

**4. Sister Margaret O'Brien** (Nun & Theologian)
- HP: 11, SAN: 80, POW: 80
- Strengths: Religion, Psychology, Persuasion
- Ideal for: Social interaction and faith-based challenges

### ✅ Rule Implementation Details

#### Skill System
- Automatic skill → characteristic mapping
- Normalized skill names (spaces → underscores)
- Falls back to characteristic value if skill missing
- Examples: investigate (INT), dodge (DEX), occult (EDU)

#### Difficulty Modifiers
- **Normal**: target = skill value
- **Hard**: target = skill value ÷ 2
- **Extreme**: target = skill value ÷ 5

#### Sanity System
- Separate sanity check (POW) when witnessing horror
- Only applies damage on **failed** POW roll
- Success = "You maintain mental clarity"
- Failure = "You lose X sanity points"

#### Critical Results
- Critical Success: 1-5 (auto-success)
- Critical Failure: 96-00 (auto-failure)

### ✅ DM Integration

#### Prompt Engineering
- Hardcoded CoC 7e rules in system prompt
- Explicit instructions for roll detection
- Horror atmosphere guidelines
- Ending condition monitoring

#### Tag Parsing
- `[ROLL: skill/difficulty]` → Automatic skill check
- `[SANITY_CHECK: N]` → Sanity damage application
- `[END: escape|madness|death]` → Trigger ending

#### LLM Configuration
- Model: Mistral 7B (4.4GB)
- Temperature: 0.7 (balanced)
- Max tokens: 300/response
- Endpoint: http://localhost:11434

### ✅ Game Endings (5 Total)

| Ending | Trigger | Description |
|--------|---------|-------------|
| **Escape** | Player flees successfully | "You escape with the truth" |
| **Madness** | SAN reaches 0 | "Your mind shatters" |
| **The Ascended** | Player enters fissure | "You become something more" |
| **Destruction** | Player destroys lighthouse | "The lighthouse crumbles" |
| **Death** | HP reaches 0 | "You sink into the depths" |

### ✅ Story & Setting

**Point Black Lighthouse** - Base Story
- Remote Maine lighthouse
- Keeper vanished (but was already dead)
- Strange symbols + ancient fissure
- Sense of ancient awakening
- Horror escalates with investigation

### ✅ Files Created/Modified

**New Files:**
```
core/game_generative.py              # Main engine (440 lines)
games/play_generative.py             # Interactive CLI (300+ lines)
test_generative_flow.py              # Auto-play demo
test_generative_with_selection.py    # Interactive demo with selection
GENERATIVE_EDITION.md                # Complete documentation
GENERATIVE_CHANGELOG.md              # This file
```

**Modified Files:**
```
games/play_generative.py
  ├─ select_investigator()            # Character selection UI
  ├─ load_prebuilt_investigators()    # JSON loader
  ├─ json_to_investigator()           # Format converter
  └─ create_new_investigator()        # Custom character creation
```

### ✅ Technical Details

#### Performance
- First response: 5-10 seconds (model warmup)
- Subsequent responses: 2-5 seconds
- CPU: Works on standard laptop (no GPU required)
- Memory: ~6GB for Mistral 7B

#### Dependencies
- `requests` (Ollama API calls)
- No other external libraries needed

#### Error Handling
- Graceful fallback if Ollama unavailable
- Sanity damage capped at 0
- HP damage capped at 0
- Invalid skill lookups default to INT

### ✅ Testing Results

**Test 1: Character Loading**
- ✓ Loads 4 prebuilt investigators
- ✓ Normalizes skill names correctly
- ✓ Preserves stats accurately

**Test 2: Skill Checks**
- ✓ D100 rolls execute correctly
- ✓ Difficulty modifiers apply
- ✓ Critical success/failure detected

**Test 3: Sanity System**
- ✓ Sanity checks only apply on POW failure
- ✓ Correct damage amounts deducted
- ✓ Madness ending triggered at SAN=0

**Test 4: DM Integration**
- ✓ Mistral generates coherent narratives
- ✓ Detects [ROLL] tags correctly
- ✓ Detects [SANITY_CHECK] tags correctly
- ✓ Maintains horror atmosphere

**Test 5: Full Game Flow**
- ✓ Character selection works
- ✓ Game initialization succeeds
- ✓ Multiple turns play correctly
- ✓ Stats update properly

### 📋 Known Limitations

- Mistral occasionally generates extra narrative markers
- No persistent save/load between sessions
- Skills limited to ~30 core CoC skills
- Combat system not fully implemented
- No NPC dialogue options yet

### 🚀 Future Enhancements

**Priority 1:**
- [ ] Combat system (attack rolls, damage)
- [ ] NPC interactions (dialogue trees)
- [ ] Inventory management (pick up/drop items)

**Priority 2:**
- [ ] Persistent save/load
- [ ] Multiple encounters per location
- [ ] Dynamic skill progression
- [ ] Sanity recovery mechanics

**Priority 3:**
- [ ] Alternative LLMs (Llama, Phi)
- [ ] Web interface (Streamlit)
- [ ] Real-time streaming responses
- [ ] Audio narration

### 🔗 Related Systems

Coexists with:
- **Fixed Adventure Version** (`games/play_immersive.py`) - 26-entry narrative
- **Classic Version** (`games/play.py`) - Minimal interface

Can upgrade/downgrade between versions without breaking state.

---

**Status**: ✅ Fully Functional  
**Last Updated**: 2026-04-10  
**Version**: 1.0 (Release Candidate)
