# Example Scene Generation

## Status

Generating images for all test scenes. This takes ~2 minutes (35s × 3 scenes).

## Scenes Being Generated

1. **lighthouse_exterior** — Rocky Maine coast, foggy night, eerie quiet
   - Danger: 1/5 | Contamination: 10%
   - Expected: Remote lighthouse, fog, rocks, pale moonlight

2. **lighthouse_interior** — Spiral stairs, iron railings, oppressive mood
   - Danger: 2/5 | Contamination: 30%
   - Expected: Interior with stairs, rust, amber ceiling beam, dread

3. **underground_cavern** — Bioluminescent growths, alien wrongness
   - Danger: 4/5 | Contamination: 75%
   - Expected: Vast cavern, sickly cyan light, organic forms, cosmic scale

## What to Look For

### Visual Quality
- [ ] Image recognizable as pixel art (not photorealistic)
- [ ] Composition matches first-person perspective
- [ ] Depth cues present (foreground/background distinction)
- [ ] Color palette matches description

### Atmosphere
- [ ] Conveys intended mood (eerie, oppressive, alien)
- [ ] Feels like Lovecraftian horror
- [ ] Sense of scale appropriate to scene
- [ ] Unnatural/wrongness evident

### Playability
- [ ] Readable as game background
- [ ] Not too dark (can distinguish objects)
- [ ] Not too bright (maintains horror tone)
- [ ] Suitable for text overlay

## Evaluation Process

1. **Open each image** in `generated/`
2. **Run evaluation guide:**
   ```bash
   python3 evaluate_examples.py
   ```
3. **Rate each image** on criteria (1-5 scale)
4. **Record findings** in `evaluations.json`
5. **Share feedback** with prompt adjustments

## Key Questions

1. Does the visual style match what you envisioned?
2. Are the prompts generating the right kind of images?
3. What adjustments are needed (colors, composition, style)?
4. Is the quality sufficient for a text adventure game?

## Next Steps (Based on Feedback)

- ✓ If images are good: proceed to motor integration
- ! If images need tweaking: adjust prompts and regenerate
- ✗ If quality is poor: evaluate alternative models or approaches

---

**Generation started:** 2026-05-20 15:45 UTC  
**Expected completion:** ~2 minutes
