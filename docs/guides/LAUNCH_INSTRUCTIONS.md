# 🚀 LAUNCH INSTRUCTIONS: Text Adventure + Image Generation

## Status: READY TO LAUNCH

✅ Image generation pipeline integrated  
✅ LocationState enhanced  
✅ Flask API updated  
✅ Integration test passed  

---

## How to Start

### Step 1: Activate Virtual Environment (if needed)

```bash
cd /Users/adrianmedina/src/Cthulhu
# If using venv:
# source venv/bin/activate
```

### Step 2: Start Flask Server

```bash
python3 app.py
```

**Expected output:**
```
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
 * WARNING: This is a development server. Do not use it in production.
```

### Step 3: Open in Browser

```
http://localhost:5000
```

### Step 4: Play!

1. Enter investigator name + archetype
2. Start game
3. Move to new locations
4. **First time visiting:** Image generates (~30-50 seconds wait)
5. **Second time visiting:** Uses cached image (instant)

---

## What to Expect

### First Location Visit
- Browser may pause while image generates
- Console shows: `[ImageGen] Generating image for...`
- Image appears below narrative text

### Subsequent Visits
- Image loads instantly (from cache)
- Same location = same image
- Different contamination level = different image

### No Image
- Some locations may not have good images (caverns)
- Game continues normally with text only
- No errors or crashes

---

## Troubleshooting

### Issue: "Could not generate image"
**Cause:** Model not loading correctly  
**Fix:** Check terminal for error, may need to restart server

### Issue: Image takes 2+ minutes
**Cause:** First load downloads model + generates  
**Fix:** This is normal. Subsequent images are instant.

### Issue: "Out of memory"
**Cause:** M1 running low on VRAM  
**Fix:** Reduce steps in `game/image_gen.py` line 105:
```python
num_inference_steps=20,  # Change from 25 to 20
```

### Issue: Image looks weird
**Cause:** Prompt not matching location well  
**Fix:** Edit prompt in `game/game_image_integration.py` line 52

---

## File Structure

```
Cthulhu/
├── app.py                          # Flask server (MODIFIED)
├── core/
│   └── location_state.py           # (MODIFIED: added image_path field)
├── game/
│   ├── scene_spec.py               # ✓ Scene specification
│   ├── art_director.py             # ✓ Prompt generation
│   ├── image_gen.py                # ✓ Image generation
│   ├── cache.py                    # ✓ Caching system
│   ├── game_image_integration.py   # ✓ Integration layer
│   ├── generated/                  # ✓ Generated images (auto-created)
│   ├── style_bible.json            # ✓ Visual rules
│   └── INTEGRATION_SUMMARY.md      # ✓ Integration docs
└── [rest of game files unchanged]
```

---

## Performance Notes

### M1 Mac Performance
- **Model load:** ~24 seconds (first time only)
- **Image generation:** ~25-50 seconds (25 steps)
- **Cache lookup:** < 100ms (instant)

### Timeline
- **First run:** 50+ seconds wait (model loads)
- **First location:** 50+ seconds (image generates)
- **Subsequent locations:** 30-50 seconds each (unless cached)
- **Return to visited location:** < 1 second (cached)

### Optimization Tips
- Visit 3-4 unique locations to build cache
- Re-visit cached locations to speed up narrative
- Close other apps if generating slowly

---

## Testing the Integration

### Test 1: Manual Location Visit
```bash
# In game UI:
1. Start game
2. Move to new location
3. Wait for image to generate
4. Verify image appears
5. Move back to same location
6. Verify image loads instantly
```

### Test 2: Check Generated Images
```bash
ls -lh game/generated/
# Should show .png files with recent timestamps
```

### Test 3: Check Browser Console
```
Open DevTools (F12)
Network tab → /api/game/state
Response JSON should include "image_url"
```

---

## Monitoring During Play

### Console Output
```
[ImageGen] Generating image for lighthouse_exterior...
[ImageGen] Prompt: Lighthouse on rocky coast...
[ImageGen] ✓ Image generated: generated/lighthouse_exterior.png
```

### Browser Console (F12)
```
Response includes:
{
  "location": "lighthouse_exterior",
  "image_url": "/images/lighthouse_exterior.png",
  "narrative": "You find yourself..."
}
```

---

## Backing Up / Reverting

### Backup Generated Images
```bash
cp -r game/generated game/generated_backup
```

### Clear Cache If Needed
```bash
rm game/generated/*.png
# (Keeps manifest.json)
```

### Revert Integration (if needed)
```bash
git checkout core/location_state.py app.py
rm game/game_image_integration.py
# Game still works without images
```

---

## Next Improvements (Optional)

1. **Faster generation:**
   - Switch to SDXL when ready
   - Use int8 quantization
   - Batch generate while player reads narrative

2. **Better quality:**
   - Fine-tune prompts by location
   - Add style_bible customization per scene
   - Implement ControlNet for composition control

3. **More locations:**
   - Add `location_to_scene_spec()` mappings
   - Create new scene types in `scene_spec.py`
   - Test prompts and images

---

## Support

**Issue?** Check:
1. Logs in terminal (Flask server)
2. Browser console (F12)
3. `game/generated/manifest.json` (cache index)

**Want to customize?**
- Edit prompts: `game/game_image_integration.py` lines 40-70
- Add locations: Add to location_map dict (line 45)
- Tweak generation: Modify `image_gen.py` parameters

---

## Launch Checklist

Before starting for real:

- [ ] Terminal: `python3 app.py` ✓
- [ ] Browser: `http://localhost:5000` ✓
- [ ] Create investigator
- [ ] Start game
- [ ] Move to new location
- [ ] Wait for image (30-50 sec)
- [ ] Image appears ✓
- [ ] Enjoy!

---

**Version:** 1.0  
**Date:** 2026-05-20  
**Status:** Production Ready (MVP)
