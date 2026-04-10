# Quick Reference Card - Alone Against the Dark

**Print this out and keep it by your side during gameplay.**

---

## Commands at a Glance

| Command | Usage | Example |
|---------|-------|---------|
| **[action]** | Describe what you do | `examine the door` |
| **[i]nventory** | Check your items | `i` |
| **[u]se item** | Use an item | `use flashlight` |
| **[d]rop item** | Drop an item | `drop notebook` |
| **[s]tatus** | View full stats | `s` |
| **[h]elp** | Show commands | `h` |
| **talk to NPC** | Speak to character | `talk to warner` |
| **ask NPC about** | Ask a question | `ask armitage about symbols` |
| **[q]uit** | Exit game | `q` |

---

## Character Stats

### Characteristics
- **STR** (Strength) - Physical power
- **CON** (Constitution) - Endurance
- **DEX** (Dexterity) - Coordination
- **INT** (Intelligence) - Intellect
- **APP** (Appearance) - Charisma
- **POW** (Power) - Willpower
- **EDU** (Education) - Knowledge
- **SIZ** (Size) - Physical mass

### Derived Stats
- **HP** - Hit Points (0 = DEATH)
- **SAN** - Sanity (0 = MADNESS)
- **Luck** - Fortune modifier

---

## Skill Check Rules

### The Roll
```
1. DM describes situation
2. "Press ENTER to test your fate"
3. You press ENTER
4. Roll d100 (1-100)
5. Result: ✓ SUCCESS or ✗ FAILURE
```

### Difficulty Modifiers
| Difficulty | Modifier | Target |
|------------|----------|--------|
| Normal | x1 | Roll vs Skill |
| Hard | ÷2 | Roll vs (Skill/2) |
| Extreme | ÷5 | Roll vs (Skill/5) |

### Special Results
- **1-5**: CRITICAL SUCCESS (guaranteed)
- **96-00**: CRITICAL FAILURE (guaranteed)

---

## Available NPCs

### Lt. William Warner (Coast Guard Officer)
- **Turns**: 1-4 (early game)
- **Knows**: Keeper's disappearance, strange sounds
- **Talk to**: `talk to warner`

### Dr. Henry Armitage (Professor)
- **Turns**: 3+ (mid-game onward)
- **Knows**: Ancient symbols, rituals, lore
- **Talk to**: `talk to armitage`

---

## Items

| Item | Command | Effect |
|------|---------|--------|
| Flashlight | `use flashlight` | Light source |
| Revolver | `use revolver` | Combat weapon |
| Rope | `use rope` | Climbing tool |
| Dynamite | `use dynamite` | Explosive |
| Holy Water | `use holy_water` | Repel creatures |
| Notebook | `use notebook` | Record findings |
| Logbook | `use logbook` | Read keeper's entries |
| Ancient Text | `use ancient_text` | Decipher symbols |

---

## Enemies

### Deep One Hybrid
- **HP**: 12
- **Skill**: 45
- **Damage**: 1d6
- **Weakness**: Firearms, combat

### Animated Corpse
- **HP**: 8
- **Skill**: 30
- **Damage**: 1d4
- **Weakness**: Anything, easily destroyed

### Shadow Entity
- **HP**: 20
- **Skill**: 60
- **Damage**: 1d8
- **Weakness**: Holy objects, light

---

## Combat Flow

```
Enemy appears
  ↓
You attack (skill check)
  ↓
On success → Deal 2-6 damage
On failure → Miss, no damage
  ↓
Enemy counter-attacks (auto)
  ↓
Take 1-8 damage (varies by enemy)
  ↓
Repeat until: Enemy HP = 0 OR Your HP = 0
```

---

## Game Endings

| Ending | Trigger | Outcome |
|--------|---------|---------|
| **ESCAPE** | Flee successfully | You survived but traumatized |
| **MADNESS** | SAN reaches 0 | Mind breaks, institutionalized |
| **DEATH** | HP reaches 0 | Character dies |
| **DESTRUCTION** | Destroy lighthouse | Structure collapses, you escape |
| **THE ASCENDED** | Embrace transformation | You become something other |

---

## Status Bar Reference

### HP Bar
```
♥♥♥♥♥♡♡♡♡♡ = 5 HP remaining
13 full hearts = 13 HP
```

### SAN Bar
```
█████░░░░░░░░░░░ = 50 SAN remaining
Full bar = 100 SAN
Half bar = 50 SAN
Empty = 0 SAN (MADNESS!)
```

---

## Model Selection Guide

| Model | Speed | Quality | Memory | Pick If |
|-------|-------|---------|--------|---------|
| **Mistral 7B** | 5-7s | ⭐⭐⭐⭐⭐ | 8GB | Want best story |
| **Neural Chat** | 3-4s | ⭐⭐⭐⭐ | 5GB | Want balance |
| **Orca Mini** | 1-2s | ⭐⭐⭐ | 3GB | Want speed |

---

## Common Skills

### Physical
- **Climb** → Scaling walls, cliffs
- **Dodge** → Avoid attacks
- **Fight** → Melee combat
- **Firearms** → Shooting weapons
- **Swim** → Water crossing
- **First Aid** → Medical care

### Investigation
- **Investigate** → Examine scenes
- **Spot Hidden** → Find concealed items
- **Navigate** → Find directions
- **Psychology** → Read people

### Knowledge
- **Occult** → Understand magic
- **Library Use** → Research books
- **Science** → Technical knowledge
- **Religion** → Religious lore

### Social
- **Persuade** → Convince people
- **Psychology** → Detect lies

---

## Tips

### For Survival
- ✓ Use items strategically
- ✓ Talk to NPCs for clues
- ✓ Investigate locations thoroughly
- ✗ Don't overconfidently charge enemies
- ✗ Don't stare at cosmic horror too long (SAN damage)

### For Story
- ✓ Read DM narration carefully
- ✓ Make thematic choices
- ✓ Explore multiple paths
- ✗ Rush through scenes
- ✗ Ignore atmospheric details

### For Rolls
- ✓ Roll when risking something
- ✓ Think before acting
- ✓ Plan your approach
- ✗ Always charge headfirst
- ✗ Attempt impossible odds

---

## Quick Start (First Game)

1. **Start Game**: `python3 games/play_generative.py`
2. **Select Model**: Choose `1` (Mistral 7B)
3. **Choose Character**: Pick `1` (Morgan the Detective)
4. **Read Opening**: Soak in the atmosphere
5. **Explore**: "I look around carefully"
6. **Roll When Needed**: Press ENTER when prompted
7. **Manage HP/SAN**: Check `[s]tatus` if worried
8. **Reach Ending**: Die, go mad, escape, or ascend

---

## Debug Commands

**These are for testing only:**

```bash
# Test a single model
python3 test_gameplay.py

# Run full playthroughs
python3 full_playthrough.py
```

---

## Need Help?

- **In-game**: Type `[h]elp` to show commands
- **Full Guide**: Read `GAMEPLAY_GUIDE.md`
- **Technical**: Check `IMPLEMENTATION_SUMMARY.md`
- **Status**: See `MODEL_COMPARISON.md`

---

**Welcome to Point Black Lighthouse.**  
**The light blinks red.**  
**Something ancient awaits.**

*Play responsibly. Save often. Trust nothing.*
