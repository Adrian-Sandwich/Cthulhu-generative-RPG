# Alone Against the Dark: Generative Edition

**A Call of Cthulhu 7e RPG with an AI Dungeon Master**

---

## ⚡ Quick Start

```bash
# Make sure Ollama is running first
ollama serve

# In another terminal
cd /Users/adrianmedina/src/Cthulhu
python3 games/play_generative.py
```

Then:
1. Choose your LLM model (Mistral 7B recommended)
2. Pick an investigator (prebuilt or custom)
3. Press ENTER to begin your investigation
4. Type actions in natural language

---

## What Is This?

A text-based RPG where:
- **You** play an investigator at Point Black Lighthouse
- **An AI** (powered by local Mistral 7B) is your Dungeon Master
- **You control when to roll the dice** - like a tabletop RPG
- **Your choices matter** - the AI adapts to your decisions
- **Horror unfolds** - cosmic dread grows as you explore

**Status**: ✅ Complete & Tested - Ready for Extended Play

---

## Key Features

### 🎲 Interactive Skill Checks
Player-controlled rolling where YOU decide when to roll:
```
DM: "You attempt to climb the crumbling staircase..."
    Press ENTER to test your fate
[You press ENTER]
✓ SUCCESS! Roll 42 vs 45 (Climb)
```

### 🎬 Proper Ending Sequences (5 endings)
- ESCAPE - You survive but traumatized
- MADNESS - Your mind shatters (SAN = 0)
- DEATH - You die (HP = 0)
- DESTRUCTION - Destroy the lighthouse
- THE ASCENDED - You transform

### 👥 NPC Dialogue
Talk to Lt. Warner and Dr. Armitage - they remember your conversations

### 📦 Inventory System
Collect & use 8 items: flashlight, revolver, rope, dynamite, holy water, logbook, ancient text, notebook

### ⚔️ Combat System
Full combat with enemy HP tracking, damage rolls, and AI counter-attacks

### 💔 Sanity & HP Tracking
Witness cosmic horror → lose SAN. Take damage → lose HP. Reach 0 → game over.

---

## Test Results

✅ **ALL TESTS PASSED**

### Playthroughs Completed
- **Mistral 7B**: 8 turns in 142s (17.8s/turn) ✓
- **Neural Chat 7B**: 8 turns in 157s (19.7s/turn) ✓
- **Orca Mini 3B**: 8 turns in 109s (13.7s/turn) ✓

**Total**: 24 turns across 3 models - zero crashes, zero errors

### Feature Validation
- ✅ Interactive rolling
- ✅ Ending narrative generation
- ✅ NPC dialogue
- ✅ Inventory management
- ✅ Combat system
- ✅ Sanity checks
- ✅ HP damage system

---

## Documentation

- **GAMEPLAY_GUIDE.md** - Complete guide with examples
- **QUICK_REFERENCE.md** - Print-friendly command reference
- **TEST_RESULTS.md** - Full test results & metrics
- **IMPLEMENTATION_SUMMARY.md** - Technical details
- **MODEL_COMPARISON.md** - Performance comparison

---

## Commands

| Command | Usage |
|---------|-------|
| `[action]` | Describe what you do |
| `[i]` | Check inventory |
| `[u] item` | Use an item |
| `[d] item` | Drop an item |
| `[s]` | View character stats |
| `talk to npc` | Speak to character |
| `[h]` | Show help |
| `[q]` | Quit game |

---

## Model Selection

| Model | Speed | Quality | Memory | Best For |
|-------|-------|---------|--------|----------|
| **Mistral 7B** | 5-7s | ⭐⭐⭐⭐⭐ | 8GB | Story immersion |
| **Neural Chat 7B** | 3-4s | ⭐⭐⭐⭐ | 5GB | Balanced play |
| **Orca Mini 3B** | 1-2s | ⭐⭐⭐ | 3GB | Speed testing |

---

## Requirements

- macOS/Linux/Windows
- Python 3.8+
- Ollama installed & running
- 3-8GB RAM (model-dependent)

## Setup

```bash
# Download models (choose at least one)
ollama pull mistral
ollama pull neural-chat
ollama pull orca-mini

# Run game
python3 games/play_generative.py
```

---

## Project Status

**Version**: 1.1.1  
**Date**: April 10, 2026  
**Status**: ✅ Production Ready  

All features implemented, tested, and validated. Ready for extended playtesting and user sessions.

---

## Next Steps

1. **Play**: `python3 games/play_generative.py`
2. **Learn**: Read `GAMEPLAY_GUIDE.md`
3. **Reference**: Use `QUICK_REFERENCE.md`
4. **Verify**: See `TEST_RESULTS.md`

---

**Welcome to Point Black Lighthouse. The light blinks red. Something ancient stirs.**
