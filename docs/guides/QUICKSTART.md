# ⚡ QUICK START GUIDE

## Play the Game Now

```bash
python3 play.py
```

Then:
1. **Select Character**
   - Dr. Eleanor Woods (Female Archaeologist) ← Recommended
   - Dr. Ellery Woods (Male Archaeologist)
   - Create your own investigator

2. **Start the Adventure**
   - Read Entry #1 description
   - Choose your action
   - Continue through the story

3. **Make Choices**
   - Game shows available options
   - Your choices affect the story
   - Some require skill/sanity checks

4. **Survive**
   - HP: Health points (0 = death)
   - SAN: Sanity points (0 = permanent madness/game over)
   - LUCK: Precious resource, spend after rolls to succeed

## What Works ✅

- ✅ 219 adventure entries fully loaded
- ✅ 340+ branching choices
- ✅ Character creation with 9 occupations
- ✅ 2 pre-generated investigators (Eleanor & Ellery Woods)
- ✅ Complete CoC 7th Edition rules
- ✅ Dice rolling system (d100 percentile)
- ✅ Skill checks with difficulty levels
- ✅ Sanity system with horror encounters
- ✅ Database persistence (save/load)
- ✅ Full game loop

## Features

### Mechanics
- **Skill Checks**: Roll d100 vs skill value (with difficulty modifiers)
- **Sanity System**: Lose SAN witnessing horrors, 0 SAN = game over
- **Luck Points**: Spend after rolling to turn failures into successes
- **34+ Skills**: From Archaeology to Survival

### Characters
- 9 professional occupations
- 8 characteristics (STR, CON, POW, DEX, APP, EDU, SIZ, INT)
- Derived stats: HP, SAN, LUCK, MP
- Skill allocation: occupation base + 70 bonus points

### Adventure
- 219 playable locations/encounters
- Multiple story branches and endings
- Investigation, exploration, survival
- 1920s setting in Esbury, Massachusetts

## File Structure

```
/Users/adrianmedina/src/Cthulhu/
├── play.py                      ← START HERE
├── game_engine.py               Core game logic
├── pregenerated_characters.py   Dr. Eleanor & Dr. Ellery Woods
├── adventure_data.json          All 219 story entries
├── CoC_RULESET.md              Complete rules reference
├── README.md                    Full documentation
└── game.db                      (auto-created) Game database
```

## Test the Engine

```bash
python3 test_full_game.py
```

Shows:
- Character loading
- Session management
- Entry navigation
- Skill checks
- Database persistence

## Troubleshooting

**"No choices available"**
- Some entries are dead ends or lead automatically
- This is intentional (story design)

**"Character stuck"**
- Save/load system works
- Can restart with different choices
- Database persists progress

**"Dice not rolling"**
- Test with: `python3 demo.py`
- Should show multiple dice results

## Next Steps

1. Play a full session (takes 1-2 hours)
2. Try different characters
3. Explore multiple endings
4. Check README.md for advanced features

---

**Created**: 2026-04-09  
**Status**: Fully playable, Phase 1 complete  
**Ready for**: Testing, playing, extending
