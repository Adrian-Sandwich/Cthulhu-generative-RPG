# Prompt Strategy Analysis

## Problem Identified

The current `spec_to_prompt()` generates prompts that are **too long** (700+ chars), which exceeds CLIP's 77-token limit and gets truncated.

### Example: Underground Cavern

**Current approach (TRUNCATED):**
```
Retro pixel-art horror game background. vast underground cavern with organic cave formations. 
Mood: cosmic wrongness, non-euclidean, inhuman scale. Sense of immediate threat, hostile presence 
implied, Reality-breaking geometry, impossible angles, non-euclidean structure, Lighting: 
glowing_crystals_and_pools, sickly_cyan_green light, unnatural intensity. Visible elements: 
jagged_crystal_formations (glowing), luminescent_pool (still_glowing), bone_white_structures 
(arranged), pulsing_fungal_masses (organic), cave_walls (carved_wrong). Color palette: 
sickly_green, deep_cyan, bone_white, void_black. Camera: wide_eye_level, first-person perspective. 
4:3 aspect ratio. Cohesive oppressive atmosphere. Game asset quality. No characters, no UI, 
no text overlays. Playable and readable game background.
```
→ **801 characters** → **Truncated to 77 tokens** → Lost detail

---

## Solution: Hierarchical Prompt Strategy

Instead of one long prompt, use a **priority-based approach**:

### Priority Tier 1: ESSENTIAL (always fits, < 50 tokens)
```
Pixel art horror game. [Location]. [Mood]. First-person view.
```

### Priority Tier 2: DETAIL (when space available, < 77 tokens total)
```
[Location details]. [Key objects]. [Lighting]. [Color palette].
```

### Priority Tier 3: REFINEMENT (for quality improvement)
```
[Contamination effects]. [Camera angle]. [Atmosphere].
```

---

## Rewritten Prompt Examples

### Cavern (Concise Version)
**OLD:** 801 chars (truncated)
```
Retro pixel-art horror game background. vast underground cavern with organic cave formations...
```

**NEW:** 98 chars (fits completely)
```
Pixel art horror cave. Glowing cyan crystals and pools. Bone structures. First-person. Dark.
```

**Token count:** ~18 tokens ✓ (within 77-token CLIP limit)

---

### Lighthouse Interior (Concise Version)
**OLD:** 728 chars
```
Retro pixel-art horror game background. interior of old lighthouse with spiral stairs...
```

**NEW:** 85 chars
```
Pixel art. Spiral stairs, iron railings, amber light. Oppressive stone tower interior. Dark.
```

**Token count:** ~16 tokens ✓

---

### Lighthouse Exterior (Concise Version)
**OLD:** 582 chars
```
Retro pixel-art horror game background. remote lighthouse on rocky Maine coast...
```

**NEW:** 72 chars
```
Pixel art. Remote lighthouse on rocky coast. Foggy night. Ominous waves. Pale light.
```

**Token count:** ~14 tokens ✓

---

## Recommended Approach

### Option A: Minimal Effective Prompts (FAST)
- **Length:** 80-120 chars
- **Token count:** 12-20 tokens
- **Generation time:** 25-30 steps, ~30s
- **Best for:** Quick iteration, testing
- **Risk:** Might lose some detail

### Option B: Detailed But Concise (BALANCED) ← RECOMMENDED
- **Length:** 150-200 chars
- **Token count:** 25-35 tokens
- **Generation time:** 30-40 steps, ~35-40s
- **Best for:** Production scenes
- **Advantage:** Good quality without truncation

### Option C: Full Detail + Advanced Techniques (SLOW)
- **Length:** 300-400 chars
- **Token count:** 50-70 tokens
- **Add:** negative_prompt engineering, seed control, guidance scale tuning
- **Generation time:** 40-50 steps, ~45-60s
- **Best for:** Hero scenes, key moments

---

## Refactoring plan_to_prompt()

### Current (Broken)
```python
def spec_to_prompt(spec, style_bible) -> tuple:
    # Builds monster 700+ char prompt
    # Gets truncated by CLIP
    # Loses key details
```

### Proposed (Tiered)
```python
def spec_to_prompt_v2(spec, style_bible) -> tuple:
    # Tier 1: Location + mood (mandatory)
    # Tier 2: Objects + lighting (if space)
    # Tier 3: Refinements (if space)
    # Result: Always under 77 tokens
```

---

## Testing Results

See `cavern_test_*.png` for comparisons:
1. **test_1:** Very concise (98 chars)
2. **test_2:** Balanced (115 chars)
3. **test_3:** With refinements (120 chars)

**Goal:** Find sweet spot for quality vs. length.

---

## Next Steps

1. ✓ Generate test prompts at different lengths
2. Evaluate which length gives best results
3. Refactor `art_director.py` to use tiered approach
4. Regenerate all example scenes with optimized prompts
5. Test integration with game engine

---

## Key Insight

**The model doesn't need 700+ chars to generate good images.**  
A well-written **100-char prompt** beats a truncated 800-char prompt every time.

Quality comes from:
1. Specific keywords (crystal, pool, stone)
2. Clear mood (dark, oppressive, alien)
3. Format clarity (first-person, pixel art)

NOT from repetition and verbosity.
