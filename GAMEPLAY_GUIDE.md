# Alone Against the Dark: Generative Edition - Gameplay Guide

**Your journey into cosmic horror awaits.**

---

## Before You Start

### System Requirements
- **Ollama Running**: Make sure Ollama is installed and running (`ollama serve`)
- **Models Downloaded**: At least one of Mistral, Neural Chat, or Orca Mini
- **Python 3.8+**: For running the game

### Quick Setup
```bash
# Ensure Ollama is running
ollama serve

# In another terminal, start the game
cd /Users/adrianmedina/src/Cthulhu
python3 games/play_generative.py
```

---

## Game Start

### 1. Model Selection
When the game starts, you'll be asked to choose your LLM model:

```
SELECT LLM MODEL

OPTIONS:

  1) Mistral 7B (Best Quality)
     • Best quality narration
     • Rich descriptions & atmosphere
     • 5-7 seconds per turn
     • Recommended: Story immersion

  2) Neural Chat (Balanced)
     • Good quality & balance
     • Fast & engaging responses
     • 3-4 seconds per turn
     • Recommended: Smooth gameplay

  3) Orca Mini (Speed)
     • Very fast responses
     • Good coherence, more concise
     • 1-2 seconds per turn
     • Recommended: Quick playthroughs
```

**Choose wisely!** Your model selection is locked for this session. You can pick a different model for your next game.

**Recommendation**: First-time? Choose **Mistral 7B** for the best story experience. In a hurry? Choose **Orca Mini**.

### 2. Investigator Selection
Next, choose your character:

```
SELECT YOUR INVESTIGATOR

OPTIONS:

  0) Create a new investigator
  1) Morgan                     - Detective
  2) Dr. Chen                   - Scientist
  3) Captain Redford            - Naval Officer
  4) Sister Margaret            - Nun
```

**Prebuilt Characters**: Each has unique skills, occupations, and backstories.
**Custom Character**: Build your own with custom name and occupation.

### 3. Story Opening
The game begins with a dramatic opening narrative explaining your arrival at Point Black Lighthouse.

---

## How to Play

### Basic Commands

#### Taking Actions
Simply describe what you do in natural language. The DM will respond.

```
➜ I approach the lighthouse cautiously

🌊 The fog thickens as you move closer. The iron door is massive, 
corroded by salt water and age. You notice fresh scratches around 
the lock—something tried to break in. Or out.
```

#### Skill Checks (The Interactive Roll System)
When you attempt something risky or uncertain, the DM will ask for a roll:

```
DM: "You attempt to climb the crumbling spiral staircase..."
    Press ENTER to test your fate

[User presses ENTER]

⚔️ ════════════════════════════════════════════════════════════════════════════
✓ SUCCESS! Roll 42 vs 45 (Climb skill)
════════════════════════════════════════════════════════════════════════════

The stairs hold. You reach the second floor.
```

**How it works**:
1. DM describes the situation and what you're attempting
2. Game displays "Press ENTER to test your fate"
3. You press ENTER whenever you're ready to roll
4. The system rolls a d100 (1-100) and compares to your skill
5. Result is displayed (✓ SUCCESS or ✗ FAILURE)
6. DM continues with the outcome

**Roll Rules** (Call of Cthulhu 7e):
- Roll 1-100
- Success if your roll ≤ your skill value
- Difficulty modifiers:
  - **Normal**: Roll vs skill (1x)
  - **Hard**: Roll vs half skill (÷2)
  - **Extreme**: Roll vs one-fifth skill (÷5)
- **Critical Success** (1-5): Extra success
- **Critical Failure** (96-00): Major failure

### Special Commands

#### [I]nventory
Check what you're carrying:

```
➜ i

INVENTORY

  • Flashlight — Casts light in darkness
  • Notebook — For recording findings
  • Revolver (.38) — 6-shot pistol

Press ENTER to continue...
```

#### [U]se Item
Use an item from your inventory:

```
➜ use flashlight

USING ITEM

You turn on the flashlight. The beam cuts through the darkness, 
revealing... shadows within shadows.

Press ENTER to continue...
```

**Available Items**:
- `flashlight` - Light source
- `revolver` - Combat weapon
- `rope` - Climbing/escape tool
- `dynamite` - Explosive
- `holy_water` - Repel creatures
- `notebook` - Record findings
- `logbook` - Read keeper's entries
- `ancient_text` - Decipher symbols

#### [D]rop Item
Remove an item from inventory:

```
➜ drop notebook

DROPPING ITEM

You drop: Notebook

Press ENTER to continue...
```

#### [S]tatus
View full character statistics:

```
➜ s

CHARACTER STATUS

Name: Morgan
Occupation: Detective

CHARACTERISTICS:
  STR: 065  CON: 060  DEX: 065  INT: 080
  APP: 060  POW: 070  EDU: 075  SIZ: 060

DERIVED:
  HP: 013  SAN: 070  Luck: 050

Turns: 5

Press ENTER to continue...
```

#### [H]elp
Show all commands:

```
➜ h

COMMANDS:
  [action]          Describe what you do (e.g., "examine the door", "run away")
  [i]nventory       Check your inventory
  [u]se [item]      Use an item (e.g., "use flashlight", "use revolver")
  [d]rop [item]     Drop an item (e.g., "drop notebook")
  [s]tatus          Full character status
  [h]elp            Show this help
  [q]uit            Quit game

Type your action in natural language. The DM will respond.
Talk to NPCs by saying: "talk to warner", "ask armitage about...", etc.
```

#### [Q]uit
Exit the game (you'll be asked to confirm):

```
➜ q

Quit game? (y/n): y

The lighthouse light fades behind you.
But you know the truth now...
```

---

## NPC Dialogue

### Talking to Characters
You can talk to NPCs who are present:

```
➜ talk to warner

NPC DIALOGUE

Lt. William Warner: "The keeper vanished three weeks ago. The light kept
blinking on its own. I've never seen anything like it. Something's very
wrong with this place."

Press ENTER to continue...
```

### Available NPCs

**Lt. William Warner** (Coast Guard Officer)
- Available: Early in the game
- Knows: Keeper's disappearance, strange sounds, lighthouse history
- Personality: Professional but visibly shaken

**Dr. Henry Armitage** (Miskatonic University Professor)
- Available: Mid-game onward
- Knows: Ancient symbols, ritual sealing, occult dangers
- Personality: Academic, grave, measured tones

### Question Examples
```
talk to warner
ask warner what he knows
ask armitage about the symbols
talk to armitage
```

---

## Combat System

### Combat Starts
When you encounter a creature, combat begins automatically:

```
DM: "A creature emerges from the darkness! [COMBAT_START: deep_one_hybrid]"

⚔️  Combat started: Deep One Hybrid (HP: 12)
```

### Combat Round
When in combat, attack actions trigger skill checks:

```
➜ attack with revolver

SKILL CHECK
Skill: FIREARMS_REVOLVER
Difficulty: NORMAL

Roll the dice... Press ENTER to test your fate
[User presses ENTER]

💚 ════════════════════════════════════════════════════════════════════════════
✓ SUCCESS! Roll 35 vs 35 (Firearms_revolver skill)
════════════════════════════════════════════════════════════════════════════

COMBAT ROUND

You hit! The creature takes 4 damage.
Deep One Hybrid strikes! You take 2 damage.
```

### Enemy Types

**Deep One Hybrid**
- HP: 12
- Skill: 45
- Damage: 1d6
- Description: Humanoid but wrong, scales and gill slits

**Animated Corpse**
- HP: 8
- Skill: 30
- Damage: 1d4
- Description: Rotting body moved by dark magic

**Shadow Entity**
- HP: 20
- Skill: 60
- Damage: 1d8
- Description: Pure shadow, barely visible

### Combat Mechanics
1. **Player Attacks**: Use skill checks (Firearms, Brawl, Fight)
2. **Damage**: Roll determines damage (2-6 typically)
3. **Enemy Counter**: Enemy rolls to attack you
4. **Damage Taken**: Reduces your HP
5. **Victory**: Enemy HP reaches 0
6. **Defeat**: Your HP reaches 0 (ending)

---

## Health & Sanity

### HP (Hit Points)
- Starts at ~10-15 depending on character
- Reduced by combat damage, environmental hazards, wounds
- Tracked with heart symbol bar: ♥♥♥♡♡♡♡♡♡♡
- When HP reaches 0: **DEATH ENDING**

### SAN (Sanity)
- Starts at ~70
- Reduced by witnessing cosmic horror (1-10 typically)
- Tracked with bar: █████████░░░░░░░░░░░
- When SAN reaches 0: **MADNESS ENDING**

### Character Status Display
Every turn shows your current state:

```
────────────────────────────────────────────────────────────────────────────────
Morgan (Detective)
  HP: [♥♥♥♥♥♡♡♡♡♡] 5    │  SAN: [█████░░░░░░░░░░░] 50    │  Luck: 50
  Location: Point Black Lighthouse - Second Floor
────────────────────────────────────────────────────────────────────────────────
```

---

## Game Endings

### 5 Possible Endings

**1. ESCAPE**
- Condition: Successfully flee the lighthouse
- Narrative: Literary description of your escape
- Tone: Bittersweet - you survived but know terrible secrets

**2. MADNESS**
- Condition: SAN reaches 0
- Narrative: Your mental deterioration
- Tone: Psychological horror - your mind breaks

**3. DEATH**
- Condition: HP reaches 0
- Narrative: Your final moments
- Tone: Dark and tragic

**4. DESTRUCTION**
- Condition: Destroy the lighthouse (if possible)
- Narrative: The structure crumbles
- Tone: Pyrrhic victory - you stopped it but at great cost

**5. THE ASCENDED**
- Condition: Embrace transformation
- Narrative: You become something other
- Tone: Cosmic - you're no longer human

### Ending Display
When a game ends, you receive a 3-paragraph literary conclusion:

```
════════════════════════════════════════════════════════════════════════════════
GAME OVER - MADNESS
════════════════════════════════════════════════════════════════════════════════

Your mind fractures like porcelain. The lighthouse keeper's whispers follow you
into the darkness, and you realize with crystalline clarity that some truths,
once glimpsed, can never be forgotten—nor forgiven.

The asylum walls are white. The orderlies speak in hushed tones. You don't
recognize them. You recognize only the voices—the things that speak from
beneath the waves, calling to you.

You will spend your remaining days here, raving about the red light and the
fissure. No one will believe you. No one will understand. The lighthouse still
blinks, and something ancient waits beneath its foundation.
```

---

## Tips for Success

### Skill Check Strategy
- **Risk Bold Actions**: The DM decides when rolls are needed
- **Smart Investigations**: Look carefully, ask questions
- **Combine Resources**: Use inventory items strategically
- **Talk to NPCs**: Gather information before major decisions

### Character Survival
- **Manage Sanity**: Don't look directly at cosmic horror
- **Heal Wounds**: Find first aid supplies if available
- **Combat Smart**: Use weapons before engaging barehanded
- **Escape Options**: Sometimes running is the right choice

### Story Immersion
- **Read Carefully**: The DM's words hold important clues
- **Think Rationally**: Your character is in danger
- **Stay in Character**: Make decisions your character would make
- **Slow Down**: Sometimes tension builds in silence

### Model Selection Tips
- **Story-Heavy**: Choose Mistral 7B for rich narration
- **Balanced Pace**: Choose Neural Chat for smooth 3-4s turns
- **Quick Playthroughs**: Choose Orca Mini for 1-2s responses
- **Your Preference**: Try all three, pick your favorite

---

## Common Questions

### "How many turns does a game usually last?"
Typically 10-15 turns before reaching an ending, but can vary based on your choices and luck.

### "Can I save my progress?"
Not yet—games are single-session experiences. This is a future feature.

### "What happens if I make a bad roll?"
Failure is part of the story. Bad rolls lead to interesting consequences, not instant death.

### "Can I respawn if I die?"
No—death is an ending. But you can start a new game with a different character or model.

### "Are there multiple paths?"
Yes! The AI DM adapts to your choices. Different actions lead to different stories.

### "Can I hurt NPCs?"
You can attempt anything. The DM will adjudicate the consequences.

### "What if the game freezes?"
Check that Ollama is still running. If it crashes, restart it and start a new game.

---

## Advanced Play

### Environmental Clues
- Names, dates, symbols in documents
- NPC dialogue contains lore and hints
- Item descriptions provide context
- Your own notebook records findings

### Skill Synergies
- **Occult** + **Ancient Text** = Understanding symbols
- **Library Use** + **Logbook** = Researching history
- **Psychology** + **NPC Dialogue** = Reading motivations
- **Firearms** + **Combat** = Better damage

### Psychological Pressure
- Sanity damage stacks over time
- Multiple failures compound stress
- Horror scenes trigger checks
- Isolation increases vulnerability

### Strategic Planning
- Gather information early (NPCs, documents)
- Acquire items before needing them
- Scout locations safely when possible
- Plan exit routes
- Know your limits

---

## After Your Game

### Reflecting
- What ending did you reach?
- What would you do differently?
- Which model did you prefer?
- What was the scariest moment?

### Sharing
- Tell the AI DM's story
- Discuss with others
- Compare different models
- Try different character combinations

### Next Game
- Pick a different model for contrast
- Try a new investigator
- Make bolder (or safer) choices
- See how the story branches differently

---

## Technical Details

### Session Saves
- Games are NOT saved automatically
- Closing the game ends your session
- Each new game is a fresh start

### Model Persistence
- Your chosen model runs for the entire session
- Switching models requires starting a new game
- LLM stays in VRAM during gameplay

### Performance Notes
- First action takes longer (model warmup)
- Subsequent actions are faster
- Combat adds variable latency
- Streaming shows real-time progress

---

## Support & Troubleshooting

### Ollama Not Running
```bash
# Start Ollama service
ollama serve
```

### Model Not Downloaded
```bash
# Download missing model
ollama pull mistral
ollama pull neural-chat
ollama pull orca-mini
```

### Slow Responses
- Check system RAM (need 3-8GB free)
- Verify Ollama is running
- Close other applications
- Try a smaller model (Orca Mini)

### DM Stuck or Hanging
- Wait up to 30 seconds for response
- Check Ollama logs
- Restart the game if truly hung
- Try a different model

---

**Welcome to the darkness. Your fate awaits.**

*Created with the Mistral 7B Large Language Model*
