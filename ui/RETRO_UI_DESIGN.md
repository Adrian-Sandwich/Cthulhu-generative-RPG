# Cthulhu AI Game - Retro ASCII UI Design Specification

## Visual Theme: Vintage Terminal (1980s-1990s)

### Color Palette
- **Primary**: Orange/Amber (#FF8C00 or similar terminal orange)
- **Secondary**: Neon Green (#00FF00 or terminal green)
- **Accent**: Cyan (#00FFFF)
- **Background**: Pure Black (#000000)
- **Text**: Amber/Green with high contrast

### Typography
- Font: Monospace (Courier, Monaco, or equivalent)
- Style: All-caps headers for retro feel
- Decorative characters: Box-drawing, geometric patterns

---

## Main UI Layouts

### 1. Title Screen

```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                     ✦ CALL OF CTHULHU: ALONE IN THE DARK ✦               ║
║                                                                            ║
║                            [████████████████]  50%                         ║
║                                                                            ║
║  ▸ CONTINUE  ▸ NEW GAME  ▸ LOAD GAME  ▸ SETTINGS  ▸ QUIT                 ║
║                                                                            ║
║    Press ENTER to start, or select with arrow keys                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 2. Game State Display (Top)

```
╔════════════════════════════════════════════════════════════════════════════╗
║ NAME: Dr. Nathaniel Blackwood        OCCUPATION: Occult Scholar            ║
║ ─────────────────────────────────────────────────────────────────────────  ║
║ HP: [███████░░░░░░░░░░░░] 11/14     SAN: [██████████░░░░░░░░░░] 75/99     ║
║ ─────────────────────────────────────────────────────────────────────────  ║
║ LOCATION: Lighthouse Interior        TURN: 6      MODEL: Mistral 7B        ║
║ ─────────────────────────────────────────────────────────────────────────  ║
║ INVENTORY: Flashlight  •  Notebook  •  Grimoire  •  Holy Water             ║
║ ─────────────────────────────────────────────────────────────────────────  ║
║ ACTIVE COMPANION: Chief Marsh (Police Chief)  [Healthy, Trusts You]        ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 3. Narrative Display (Center)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  🌊 THE KEEPER                                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                            │
│  The lighthouse keeper's logbook lies open on the desk. Water-damaged     │
│  pages reveal fragmentary entries from the past month. The handwriting   │
│  becomes increasingly erratic—words slurring together, repeated phrases  │
│  suggesting obsession.                                                    │
│                                                                            │
│  "They call from below. Every night, the bell rings on its own. The     │
│  sea... the sea is WATCHING."                                           │
│                                                                            │
│  The most recent entry is dated three days ago. It ends with a single   │
│  word, written so forcefully the pen nearly tore through the paper:      │
│  "MERCY"                                                                 │
│                                                                            │
│  What do you do?                                                          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 4. Keeper Thinking State (Enhanced)

```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                        ◇ THE KEEPER CONTEMPLATES ◇                        ║
║                                                                            ║
║                     Ancient patterns emerge from darkness...              ║
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────┐    ║
║  │▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  35%         │    ║
║  └──────────────────────────────────────────────────────────────────┘    ║
║                                                                            ║
║                     ⧗ The Keeper considers...                            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 5. Skill Check Dialog

```
╔════════════════════════════════════════════════════════════════════════════╗
║                          ▌ SKILL CHECK ATTEMPT ▐                          ║
║  ─────────────────────────────────────────────────────────────────────   ║
║                                                                            ║
║  SKILL: INVESTIGATE                                                       ║
║  Difficulty: NORMAL (Roll must be ≤ 60)                                   ║
║  Your Skill: 55                                                           ║
║                                                                            ║
║  ┌────────────────────────────────────────────────────────────────────┐  ║
║  │  Press SPACE to roll the dice...                                  │  ║
║  └────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  "Fate favors the prepared mind..."                                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 6. Roll Result Display

```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║  🎲 ══════════════════════════════════════════════════════════════════    ║
║  ✓ SUCCESS! (Rolled 43, needed 60)                                        ║
║  🎲 ══════════════════════════════════════════════════════════════════    ║
║                                                                            ║
║  Your keen eye catches something others would miss. Behind a loose        ║
║  panel in the keeper's quarters, you discover a leather journal bound    ║
║  with strange symbols. The paper inside is filled with fragmentary      ║
║  sketches—geometric patterns that seem to shift and twist when you      ║
║  look at them directly.                                                   ║
║                                                                            ║
║  ⚠ ✓ ITEM FOUND: Ancient Tome  [Added to inventory]                     ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 7. Sanity Check Display

```
╔════════════════════════════════════════════════════════════════════════════╗
║                        ▌ SANITY CHECK ▐                                   ║
║  ─────────────────────────────────────────────────────────────────────   ║
║                                                                            ║
║  You witness something that defies human understanding.                   ║
║                                                                            ║
║  The lighthouse beam cuts through the fog above, but down in the black    ║
║  waters below, you see something MOVE. Something vast. Something that    ║
║  shouldn't exist in any world governed by rational laws.                  ║
║                                                                            ║
║  ┌────────────────────────────────────────────────────────────────────┐  ║
║  │ Your mind reels. Roll 1d100 to resist the encroaching madness...  │  ║
║  │                                                                    │  ║
║  │ SAN before: 75    |    SAN loss: 5    |    SAN after: 70          │  ║
║  └────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  💔 You lose 5 sanity points to this nightmare vision.                    ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 8. Inventory Display

```
╔════════════════════════════════════════════════════════════════════════════╗
║                            ▌ INVENTORY ▐                                  ║
║  ─────────────────────────────────────────────────────────────────────   ║
║                                                                            ║
║  ▸ Flashlight          — Provides light in dark places (Battery: OK)      ║
║  ▸ Notebook            — Your notes on the investigation                  ║
║  ▸ Revolver            — 6 bullets remaining                              ║
║  ▸ Holy Water          — For protection against the supernatural          ║
║  ▸ Rope (50 feet)      — Useful for climbing or binding                   ║
║  ▸ Ancient Tome        — CURSED: Reading causes SAN damage                ║
║  ▸ Keeper's Journal    — Filled with cryptic entries                      ║
║                                                                            ║
║  Use: u <item>    Drop: d <item>    Read: r <item>                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 9. NPC Dialogue Display

```
╔════════════════════════════════════════════════════════════════════════════╗
║                         ▌ NPC DIALOGUE ▐                                  ║
║  ─────────────────────────────────────────────────────────────────────   ║
║                                                                            ║
║  CHIEF MARSH [Police Chief]                    Attitude: FRIENDLY (+35)   ║
║  ═══════════════════════════════════════════════════════════════════════  ║
║                                                                            ║
║  "Look, I've been in this business for twenty years. I've seen things    ║
║  that don't make sense, and I've learned not to question them. But       ║
║  this... this is different."                                             ║
║                                                                            ║
║  Chief Marsh leans against the wall, his weathered face grave.           ║
║                                                                            ║
║  "The lighthouse keeper wasn't just missing. His logbook—what we        ║
║  found—it reads like a man going mad. And then there's the blood       ║
║  in the tower. Way too much blood for anyone to survive."               ║
║                                                                            ║
║  ◇ Reputation increased (+5) ◇                                           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### 10. Game Over / Ending Screen

```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                           ▌ GAME OVER ▐                                   ║
║                                                                            ║
║                         🔮 TRIUMPH THROUGH SACRIFICE 🔮                   ║
║                                                                            ║
║  ───────────────────────────────────────────────────────────────────────  ║
║                                                                            ║
║  You made it. Against impossible odds, you uncovered the truth and        ║
║  stopped something genuinely catastrophic. Your companions survived.      ║
║  Your sanity, though tested, remains largely intact.                      ║
║                                                                            ║
║  More importantly, you've proven that human determination, intelligence,  ║
║  and courage can prevail even against cosmic horrors.                     ║
║                                                                            ║
║  ───────────────────────────────────────────────────────────────────────  ║
║                                                                            ║
║  FINAL STATISTICS:                                                        ║
║  ├─ HP:  14/14  •  SAN: 75/99  •  TURNS: 7                               ║
║  ├─ ENDING: Triumph Through Sacrifice                                    ║
║  ├─ COMPANIONS LOST: 0                                                   ║
║  └─ SECRETS DISCOVERED: 8                                                ║
║                                                                            ║
║  ═══════════════════════════════════════════════════════════════════════  ║
║                                                                            ║
║  ▸ PLAY AGAIN  ▸ SAVE SCREENSHOT  ▸ MAIN MENU                            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## Color Implementation Notes

### Terminal Color Codes (ANSI)
```
Orange/Amber:  \033[38;5;208m  or  \033[1;33m (bright yellow)
Neon Green:    \033[38;5;46m   or  \033[0;32m
Cyan:          \033[38;5;51m   or  \033[0;36m
Black:         \033[40m
White/Default: \033[0m
```

### CSS/Web Alternative
```css
/* If web version needed */
body {
  background-color: #000000;
  color: #FF8C00;
  font-family: 'Courier New', monospace;
}
```

---

## Implementation Roadmap

### Phase 1: Keeper Thinking (✓ COMPLETE)
- [x] Animated loading bar with cosmic hints
- [x] Integration with game loop
- [x] Multiple visual styles

### Phase 2: Full Retro UI
- [ ] Create `ui/retro_display.py` with color utilities
- [ ] Implement box-drawing helper functions
- [ ] Create display classes for each screen type
- [ ] Replace current print-based UI with colored/styled output
- [ ] Add transition animations between screens

### Phase 3: Advanced Features
- [ ] Screen history/scrollback
- [ ] Custom color profiles
- [ ] Terminal detection (auto-choose compatible colors)
- [ ] Accessibility options (high contrast, no colors, etc.)

---

## Box Drawing Characters

```
Single Line:    ┌─┐│└─┘
Double Line:    ╔═╗║╚═╝
Heavy:          ┏━┓┃┗━┛
Mixed:          ╭─╮│╰─╯

Corners:
  Top-Left:     ╔  ┌  ┏  ╭
  Top-Right:    ╗  ┐  ┓  ╮
  Bottom-Left:  ╚  └  ┗  ╰
  Bottom-Right: ╝  ┘  ┛  ╯
```

---

## Notes for Implementation

1. **Color Fallback**: Detect terminal capabilities and fall back to monochrome
2. **Width Handling**: Design assumes 80-character terminal width (common standard)
3. **Performance**: Avoid excessive redraws; update only changed regions
4. **Accessibility**: Provide clear keyboard shortcuts and non-color-dependent info
5. **Testing**: Test on macOS Terminal, Linux xterm, Windows Terminal

