# ALONE AGAINST THE DARK - GENERATIVE EDITION

## Overview

**Open-ended, AI-driven gameplay** with Mistral 7B running locally as your Dungeon Master.

Instead of navigating a fixed narrative tree, you interact **naturally** with an AI DM who:
- ✅ Generates dynamic narratives
- ✅ Automatically requests skill checks when needed
- ✅ Applies sanity damage for horror
- ✅ Enforces Call of Cthulhu 7e rules
- ✅ Works toward 5 defined endings

## System Requirements

### Prerequisites
```bash
# Ollama (AI model manager)
brew install ollama  # or download from https://ollama.ai

# Mistral 7B (LLM - pulls automatically)
ollama pull mistral

# Start Ollama service
ollama serve  # Keep running in background
```

### Python
- Python 3.8+
- `requests` library (auto-installed)

## How to Play

### Quick Start
```bash
cd /Users/adrianmedina/src/Cthulhu
python3 games/play_generative.py
```

### Game Flow

**1. Investigator Selection**
- Choose from 4 **preloaded investigators** (ready to play)
- OR create a **new custom investigator**
- Each preloaded character has unique skills and story hooks

**Available Investigators:**
```
1. Detective Morgan (Private Investigator)
   HP: 13, SAN: 70, POW: 70
   Skills: Investigate, Library, Persuade, Spot Hidden, Psychology

2. Dr. Elizabeth Chen (Occult Scholar)
   HP: 10, SAN: 75, POW: 85
   Skills: Library, Occult, Language (Latin), Psychology, Science (Astronomy)

3. Captain James Redford (Coast Guard Officer)
   HP: 15, SAN: 65, POW: 60
   Skills: Navigate, Survival (Sea), First Aid, Pilot (Boat), Firearms (Revolver)

4. Sister Margaret O'Brien (Nun & Theologian)
   HP: 11, SAN: 80, POW: 80
   Skills: Religion, Psychology, Persuade, Library, Occult

0. Create Custom Investigator
   Design your own character with custom stats
```

**2. Main Loop**
```
DM describes situation
↓
You describe action (natural language)
↓
DM rolls dice if needed: [ROLL: skill/difficulty]
↓
Game applies result (success/failure)
↓
DM narrates consequences + suggests sanity check
↓
Continue...
```

**3. Example Interaction**
```
DM: "You arrive at Point Black Lighthouse. The fog is thick, the keeper is missing..."

You: "I examine the lighthouse exterior for clues about what happened"

DM: "You notice strange symbols on the stone and a trail of blood..."
    [ROLL: investigate/normal]

System: Roll 42 vs investigate(60) → SUCCESS

DM: "You find a torn piece of the keeper's jacket..."
    [SANITY_CHECK: 2]

System: Make sanity check? (POW 70) → Success, no loss
```

## Skills & Mechanics

### Available Skills
```
Combat: dodge, fight, brawl
Investigation: investigate, occult, library, psychology
Physical: climb, swim, jump
```

### Difficulty Levels
- **Normal**: Roll ≤ skill value
- **Hard**: Roll ≤ (skill value ÷ 2)  
- **Extreme**: Roll ≤ (skill value ÷ 5)

### Sanity System
- Start with POW score (70)
- Witnessing horror: POW roll to resist
- Failure: Lose specified sanity points
- 0 SAN: Permanent madness → Game Over (Mad ending)

### Combat/Damage
- HP = (CON + SIZ) / 10
- 0 HP: Incapacitation → Game Over (Death ending)

## The 5 Endings

1. **ESCAPE** - Survive and flee the lighthouse
   - Condition: Successfully leave, sanity > 20
   - Message: "You escape with the truth"

2. **MADNESS** - SAN reaches 0
   - Condition: SAN = 0
   - Message: "Your mind shatters. Institutionalized..."

3. **THE ASCENDED** - Embrace transformation
   - Condition: Player willingly enters fissure
   - Message: "You become something more than human"

4. **DESTRUCTION** - Seal the lighthouse
   - Condition: Destroy fissure/mechanisms
   - Message: "The lighthouse crumbles. The barrier holds."

5. **DEATH** - HP reaches 0
   - Condition: HP = 0
   - Message: "Your body fails. You sink into the depths."

## How the DM Works

### System Prompt (Hardcoded)
The DM receives instructions including:
- **Call of Cthulhu 7e rules** fully specified
- **When to request rolls**: "Combat means roll Dodge. Locked doors mean roll Locksmith..."
- **Horror atmosphere** guidelines
- **Sanity mechanics** integrated
- **Ending conditions** to watch for

### DM Tags (Auto-Parsed)
```
[ROLL: skill/difficulty]      → System requests skill check
[SANITY_CHECK: damage]        → System applies SAN loss
[END: escape|madness|death]   → Trigger ending
```

### Example DM Prompt
```
You are the Dungeon Master for Call of Cthulhu 7th Edition.

=== RULES (ENFORCE STRICTLY) ===
- ALL skill checks are d100 (roll 1-100)
- Success: roll ≤ target number
- When a player attempts an action with risk, REQUEST A ROLL:
  Format: [ROLL: skill_name/difficulty]

=== PLAYER CHARACTER ===
Name: Detective Morgan
Skills: investigate 60, dodge 50, fight 40, ...

=== YOUR TASK ===
1. Describe what happens (2-3 sentences)
2. If action needs skill check, REQUEST it: [ROLL: dodge/normal]
3. Track atmosphere and horror
4. If witnessing horror: [SANITY_CHECK: damage]
5. Check if game ending is reached

Remember: Point Black Lighthouse holds ancient secrets.
Be atmospheric. Make choices matter.
```

## File Structure

```
core/
  ├── game_generative.py      # Main engine
  │   ├── InvestigatorState   # Player character
  │   ├── GameState           # Game progress
  │   ├── CoC7eRulesEngine    # Rule enforcement
  │   └── GenerativeGameEngine # AI DM + orchestration
  └── game_enhanced.py         # (Used for save/load utilities)

games/
  └── play_generative.py       # Interactive CLI (start here!)

test_generative_flow.py        # Demo/testing
```

## Testing

### Quick Demo (Auto-plays with default character)
```bash
python3 test_generative_flow.py
```

### Interactive Demo with Character Selection
```bash
python3 test_generative_with_selection.py
```
This tests 3 turns of gameplay while letting you choose your investigator.

### Full Interactive Game
```bash
python3 games/play_generative.py
```
Full game loop with unlimited turns until ending is reached.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│ PLAYER INPUT                                             │
│ "I climb down to the rocks"                              │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ GENERATIVE GAME ENGINE                                  │
│ • Builds DM prompt with character state                 │
│ • Calls Mistral 7B via Ollama                           │
│ • Parses response for [ROLL], [SANITY_CHECK]           │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ MISTRAL 7B (Local LLM)                                  │
│ • Generates narrative                                    │
│ • Identifies when rolls are needed                       │
│ • Maintains horror atmosphere                           │
│ • Suggests sanity checks                                │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ RULES ENGINE (CoC7eRulesEngine)                         │
│ • Executes D100 rolls                                    │
│ • Applies difficulty modifiers                          │
│ • Tracks sanity loss                                     │
│ • Checks ending conditions                              │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ GAME STATE UPDATE                                        │
│ • Update narrative                                       │
│ • Apply roll results                                     │
│ • Update HP/SAN                                          │
│ • Check for ending                                       │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ DISPLAY TO PLAYER                                        │
│ "You climb the rocks. Make a Climb check!"             │
│ "Roll: 42 vs 45 → SUCCESS"                             │
│ "You find clues... [SANITY_CHECK: 2]"                  │
└─────────────────────────────────────────────────────────┘
```

## Commands During Play

| Command | Action |
|---------|--------|
| `[natural action]` | Describe what you do |
| `[i]nventory` | Check your items |
| `[s]tatus` | View full character stats |
| `[h]elp` | Show commands |
| `[q]uit` | Save and exit |

## Example Playthrough

```
=== TURN 1 ===
You: "Examine the lighthouse exterior carefully"

DM: "You circle the structure, noticing strange symbols carved 
     into the stone. A faint blue glow emanates from cracks 
     in the foundation. The air smells of salt and something... 
     else. Something ancient."

[ROLL: investigate/normal] → Roll 58 vs 60 → SUCCESS
[SANITY_CHECK: 1] → POW roll: 72 vs 70 → FAILURE → SAN: 70→69

You lose 1 sanity from witnessing the symbols.

=== TURN 2 ===
You: "I descend to the rocks to examine the fissure"

DM: "As you reach the rocky shore, you notice the fissure is 
     far larger than you thought. Water moves impossibly—flowing 
     in directions that defy gravity. In the depths, something 
     shifts. Something intelligent."

[ROLL: climb/hard] → Roll 23 vs 30 → SUCCESS
[SANITY_CHECK: 3] → POW roll: 45 vs 70 → SUCCESS → No loss

But you're getting closer to the truth...
```

## Technical Notes

### Ollama Integration
- Calls `http://localhost:11434/api/generate`
- Model: `mistral:latest` (7B parameters)
- Temperature: 0.7 (balanced creativity + coherence)
- Max tokens: 300 per response

### Performance
- First response: ~5-10 seconds (model warming up)
- Subsequent responses: 2-5 seconds
- Depends on CPU/GPU

### Limitations
- No GPU acceleration needed (7B fits in RAM)
- Mistral is creative but may hallucinate occasionally
- Not trained on CoC rules (hence hardcoded prompt)

## Future Enhancements

- [ ] **Inventory system** - Pick up/use items during gameplay
- [ ] **NPC interactions** - Talk to townspeople, other investigators
- [ ] **Dynamic skill checks** - Different DCs based on difficulty
- [ ] **Combat system** - Initiative, turn order, multiple enemies
- [ ] **World state** - Time progression, location changes
- [ ] **Persistent saves** - Save/load mid-game
- [ ] **Multiple DMs** - Switch between Mistral, Llama, Phi

## Troubleshooting

### "Connection refused" on localhost:11434
```bash
# Start Ollama service
ollama serve
```

### Model downloads very slowly
```bash
# Pre-download Mistral
ollama pull mistral

# Check status
ollama list
```

### LLM gives bad rolls
The DM generates narratively, not mechanically. If bad rolls, check:
- Skill values in `create_investigator()` 
- Difficulty levels suggested by DM
- Sanity thresholds

### Game crashes on long gameplay
This is normal - keep game under 20-30 turns for stability.

---

**Version**: 1.0  
**Last Updated**: April 2026  
**Status**: Fully Functional ✅
