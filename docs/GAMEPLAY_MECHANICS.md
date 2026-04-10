# Gameplay Mechanics - Complete Documentation
**Date**: 2026-04-09  
**Status**: ✅ Full Implementation

## Overview

The game combines interactive fiction with full Call of Cthulhu 7th Edition mechanics. Every decision and roll affects character stats and story progression.

## Character Stats

### Pre-Generated: Dr. Eleanor Woods

| Stat | Value | Derived |
|------|-------|---------|
| STR | 50 | - |
| CON | 55 | - |
| POW | 60 | SAN = 60 |
| DEX | 65 | - |
| APP | 60 | - |
| EDU | 75 | - |
| SIZ | 45 | - |
| INT | 70 | - |
| - | - | **HP = 10** |
| - | - | **LUCK = 12** |

### Skills (Selected - Actual Values Used in Rolls)

| Skill | Value | Usage |
|-------|-------|-------|
| Archaeology | 60% | History/ancient artifacts |
| Dodge | 45% | Avoiding attacks |
| Fighting | 35% | Melee combat |
| Firearms | 30% | Ranged combat |
| Psychology | 35% | Understanding motives |
| Navigation | 50% | Finding way through darkness |
| Stealth | 35% | Sneaking past enemies |
| Listen | 40% | Hearing sounds/clues |
| Appraise | 35% | Valuing items |
| History | 45% | Historical knowledge |
| Library Use | 55% | Research |
| Climb | 55% | Physical climbing |

## Roll System

### How Rolls Work

**1. Player encounters roll option**
```
  1. Attempt Archaeology: [Archaeology roll]
  2. Try to bypass lock: [Locksmith roll]
```

**2. Player selects option → Roll menu appears**
```
🎲 ARCHAEOLOGY ROLL
======================================================================
Dr. Eleanor Woods - Skill Value: 60%

How do you want to roll?
  1. Automatic roll (system rolls d100)
  2. Manual roll (enter your d100 result)
  3. Cancel
```

**3. Player chooses roll method**

**Option 1: Automatic Roll**
- System rolls d100
- Compared against skill value
- Success if roll ≤ skill value

**Option 2: Manual Roll**
- Player rolls physical dice (d100)
- Enters result (1-100)
- System compares against skill value

**Option 3: Cancel**
- Skips roll
- Uses default navigation destination

### Example Roll Sequence

**Scenario**: Attempting to dodge gunfire

```
🎲 DODGE ROLL
======================================================================
Dr. Eleanor Woods - Skill Value: 45%

How do you want to roll?
  1. Automatic roll (system rolls d100)
  2. Manual roll (enter your d100 result)
  3. Cancel

Choose (1-3): 1

System rolled: 52

Skill Value: 45%
Roll Result: 52
❌ FAILURE!

⚠️  DAMAGE TAKEN: -4 HP (6/10)
======================================================================
```

## Skill Mapping

System maps narrative actions to character skills:

| Narrative Action | Skill Used | Character Value |
|-----------------|-----------|-----------------|
| Dodge gunfire | Dodge | 45% |
| Investigate ancient text | Archaeology | 60% |
| Understand suspect | Psychology | 35% |
| Find way in fog | Navigation | 50% |
| Move silently | Stealth | 35% |
| Listen for sounds | Listen | 40% |
| Break into safe | Locksmith | 25% |
| Research library | Library Use | 55% |
| Climb building | Climb | 55% |
| Fight enemy | Fighting | 35% |
| Shoot pistol | Firearms | 30% |

## Consequences of Failure

### Combat Failures (Dodge, Fighting)
- **Melee failure**: -1d3 HP (1-3 damage)
- **Gunfire failure**: -1d6 HP (1-6 damage)
- **Death condition**: HP ≤ 0 → Game Over

### Sanity Failures (Psychology, Sanity checks)
- **Horror encounter failure**: -1d5 SAN (1-5 sanity loss)
- **Insanity condition**: SAN ≤ 0 → Character incapacitated

### Investigation Failures
- **Missed clues**: Story branch reveals less information
- **Wrong deduction**: Story takes alternate path

## Story Branching

Success and failure lead to **completely different story paths**:

**Success Path Example**:
```
Entry 140: Joshua attacks
→ Roll Dodge
  → Success → Entry 132 (You escape)
  → Failure → Entry 96 (You're hit, need medical aid)
```

Different entries mean different encounters, discoveries, and ultimately different endings.

## Character Progression

### Resources Management

Players manage three key resources:

1. **Health Points (HP)**
   - Start: 10 (for Eleanor)
   - Reduced by: Combat failures, gunfire
   - Death at: ≤ 0

2. **Sanity Points (SAN)**
   - Start: 60 (Eleanor's POW stat)
   - Reduced by: Horror discoveries, failed psychology checks
   - Insanity at: ≤ 0

3. **Luck Points (LUCK)**
   - Start: 12 (3d6×5 rolled during character generation)
   - Can be spent to: Modify failed rolls (+1 to +10)
   - Not yet implemented but available for future use

### Real-Time Stat Tracking

Status bar always visible:
```
DR. ELEANOR WOODS | HP: 8/10 | SAN: 58/60 | LUCK: 12/12
```

Shows current/maximum for each resource.

## Supported Skills for Rolls (44 Total)

| Roll Type | Count | Examples |
|-----------|-------|----------|
| Combat (Dodge/Fighting) | 8 | Dodge gunfire, Melee combat |
| Investigation | 6 | Archaeology, Anthropology |
| Navigation | 5 | Find way, Locate target |
| Stealth | 4 | Sneak past, Hide |
| Locks/Safes | 3 | Locksmith, Breaking in |
| Sanity | 3 | Witness horror, Resist terror |
| Attributes | 6 | STR, CON, DEX, POW rolls |
| Appraisal | 2 | Value items |
| Other | 7 | Swimming, Hearing, etc. |

## Difficulty Modifiers (Future Enhancement)

System ready to support difficulty scaling:
- **Regular**: Roll ≤ skill value (currently used)
- **Hard**: Roll ≤ skill value / 2
- **Extreme**: Roll ≤ skill value / 5

## Multiple Characters

Game supports creating custom investigators with:
- Name and age
- Occupation (9 types: Archaeologist, Academic, etc.)
- Automatic stat generation
- Skill allocation per occupation

Pre-generated characters available:
- Dr. Eleanor Woods (Female Archaeologist)
- Dr. Ellery Woods (Male Archaeologist)

## Game States & Termination

Game ends when:

1. **Victory**: Reach "THE END" in story
   - Multiple victory paths available (21 unique)
   - Different outcomes based on choices/rolls

2. **Death**: HP ≤ 0
   - Failed combat rolls in dangerous situations
   - Continue playing (reset) or quit

3. **Insanity**: SAN ≤ 0
   - Failed sanity checks in horror encounters
   - Character incapacitated, game over

## Complete Gameplay Example

```
[Start Game]
↓
[Select Character] → Dr. Eleanor Woods
↓
[Entry 1: Boarding Ferry] → Press ENTER
↓
[Entry 12: Ferry Ride] → Press ENTER
↓
[Entry 3: Arriving in Esbury]
  Choose: 1. Visit estate sale, 2. Find hotel
  → Select: 1
↓
[Entry 15: Estate Sale]
  Roll: Appraise items
  → Select: Automatic roll
  → Result: 38 rolled vs 35% skill = SUCCESS
↓
[Continue navigating story...]
↓
[Entry 140: Joshua Attacks!]
  Roll: Dodge gunfire
  → Select: Manual roll (using physical d100)
  → Enter: 42
  → Result: 42 rolled vs 45% skill = SUCCESS
  → Navigate to Entry 132 (escape route)
↓
[... story continues ...]
↓
[Entry 176: THE END] ✅ VICTORY
```

## Technical Implementation

### Files Involved
- `play.py` - Main game loop and roll execution
- `game_engine.py` - Character, DiceRoller, GameSession
- `pregenerated_characters.py` - Character stats and skills
- `adventure_data.json` - Story entries with roll metadata

### Roll Metadata Format

Each roll choice stored as:
```json
{
  "text": "Attempt Archaeology:",
  "is_roll": true,
  "skill": "archaeology",
  "success_destination": 178,
  "failure_destination": 210,
  "destination": 178
}
```

### Character.skills Structure

```python
{
  'Archaeology': 60,
  'Dodge': 45,
  'Fighting': 35,
  'Firearms': 30,
  'Psychology': 35,
  'Navigation': 50,
  'Stealth': 35,
  ...
}
```

## Player Decisions Impact

Every choice affects story:

1. **Navigation choice**: Different locations, NPCs, discoveries
2. **Roll success/failure**: Branches story, damages stats
3. **Resource management**: HP/SAN affect future rolls and survival
4. **Custom character**: Different skill distribution = different success rates

## Next Enhancements (Optional)

- Luck point spending mechanics
- Hard/Extreme difficulty scaling
- Skill improvement through use
- Opposed rolls (vs. NPC skills)
- Group play with multiple characters
- Save/Load game progress

## Conclusion

The game delivers a complete tabletop RPG experience within interactive fiction. Players encounter meaningful skill checks, manage character resources, and navigate branching stories where their abilities genuinely affect outcomes.

Every roll matters. Every stat matters. Every choice matters.

