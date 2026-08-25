# DECISION POINT: Pipeline Quality vs. Practicality

## Current Status

✓ **Viability:** Confirmed (pipeline works end-to-end)  
✓ **Performance:** Acceptable (35s/image on M1)  
⚠ **Quality:** Mixed (varies by scene type)  

---

## What Works Well

### Lighthouse Scenes ✓ EXCELLENT
- **Exterior:** Clear lighthouse, rocky coast, foggy ominous mood
- **Interior:** Spiral stairs, proper perspective, creepy atmosphere
- **Why:** Model understands concrete architecture

### Why These Work
- Specific architectural vocabulary (lighthouse, stairs, railings)
- Clear perspective cues
- Recognizable real-world objects
- Simple geometry

---

## What Needs Work

### Cavern Scenes ⚠ PROBLEMATIC
- Tests 1-3: Abstract textures, maps, unclear perspective
- Test 4-6: Better but still abstract
- **Why:** Model struggles with abstract concepts + first-person simultaneously

### Why Caverns Fail
- "Cavern" is vague to the model
- "Bioluminescent" is too abstract for pixel art
- Mixing multiple abstract concepts → chaos
- First-person + alien geometry = confusing

---

## Three Paths Forward

### PATH A: Accept Current Quality (FAST, PRACTICAL)
Use what works:
- ✓ Concrete locations (lighthouse, ruins, library)
- ✓ Real architecture (towers, stairs, chambers)
- ⚠ Skip abstract caverns (use text description instead)

**Pros:**
- Ship faster (4-6 hours to integration)
- Guaranteed good results
- Easy to maintain prompts

**Cons:**
- Less visual diversity
- Can't show truly alien scenes
- Player gets no image for some locations

**Time to integration:** 4-6 hours

---

### PATH B: Fine-tune Prompts (MEDIUM, RECOMMENDED)
Use strategy document + iterate:
- Shorter, more specific prompts
- Focus on visual keywords (crystal, pool, glow)
- Drop abstract concepts
- Use "tricks" (negative prompts, guidance tuning)

**Pros:**
- Better results without changing model
- Fast feedback loop (3-4 iterations per scene)
- Maintains full location coverage

**Cons:**
- Takes time to dial in per-location
- May still have abstract scenes
- Requires experimentation

**Time to integration:** 6-8 hours (3 hours prompts + 3-5 hours integration)

---

### PATH C: Use Better Model (SLOW, PREMIUM)
Switch to SDXL or Stable Diffusion 2.1:
- Better at complex scenes
- Better image quality
- Better instruction following

**Pros:**
- Probably solves cavern problem
- Better overall quality
- More future-proof

**Cons:**
- Slower generation (2-3x)
- Larger models (8-10 GB VRAM)
- May not fit on M1 easily
- More setup/complexity

**Time to integration:** 1-2 weeks (testing + setup + iteration)

---

## Recommendation: Hybrid PATH B+A

### Phase 1: Now (4-6 hours)
1. Lock in "working" scenes (lighthouse exterior, interior)
2. Integrate with game engine
3. Test end-to-end with real gameplay

### Phase 2: Iterate (later, as needed)
1. Refine cavern/abstract prompts with feedback
2. If still bad → mark as "text-only" locations
3. User sees: "You descend into darkness..." (text) + no image

### Phase 3: Optional Polish (if time)
1. Consider SDXL if budget allows
2. Fine-tune style bible based on player feedback
3. Add more location variants

---

## Quick Wins (1-2 hours)

Even with current quality, we can improve immediately:

1. **Shorten prompts** (10 min)
   - Current: 700+ chars
   - Target: 100-120 chars
   - Benefit: Better CLIP compliance

2. **Refactor spec_to_prompt()** (15 min)
   - Use tiered approach (Priority 1, 2, 3)
   - Automatically caps at 77 tokens
   - Cleaner code

3. **Add prompt caching** (5 min)
   - Cache prompt+image mapping
   - Debug tool to see what prompt generated what image
   - Helps iterate faster

4. **Create prompt gallery** (10 min)
   - Save all prompts to JSON
   - Document which ones work/fail
   - Reference for future locations

---

## My Vote

**Go PATH B (Fine-tune Prompts):**

1. **Lighthouse scenes work NOW** → integrate immediately
2. **Cavern needs tweaking** → iterate with user feedback
3. **Full integration in 6-8 hours** → reasonable timeline

This keeps momentum while being realistic about quality.

---

## Decision Required

Choose one:

- [ ] **A) Accept quality, skip bad scenes, ship fast (4-6h)**
- [x] **B) Refine prompts, cover all locations, medium effort (6-8h)**
- [ ] **C) Upgrade model, best quality, high effort (1-2 weeks)**

What works best for your timeline?
