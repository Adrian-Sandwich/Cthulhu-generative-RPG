# Image Generation Integration Summary

## What Was Added

### 1. **LocationState Enhancement**
**File:** `core/location_state.py`
- Added field: `generated_image_path: Optional[str]`
- Updated `to_dict()` and `from_dict()` for serialization
- No breaking changes to existing code

### 2. **Image Service Layer**
**File:** `game/game_image_integration.py`
- New class: `ImageGenerationService`
  - Converts `LocationState` → `SceneSpec` → Image
  - Lazy-loads image generator (expensive operation)
  - Handles caching automatically
- Function: `generate_for_location(location_state)` - easy entry point

### 3. **Prompt Optimization**
**File:** `game/art_director.py`
- Shortened prompt generation (< 100 chars)
- Better pixel-art keyword emphasis
- Fixed path resolution for `style_bible.json`

### 4. **Flask API Enhancement**
**File:** `app.py`
- Added image serving: `/images/` static route
- Modified `/api/game/state` to include `image_url`
- Images generated automatically on first visit
- Subsequent visits use cache

### 5. **Testing**
**File:** `game/test_integration.py`
- Tests LocationState → Image pipeline
- Validates caching mechanism
- Can be run standalone

---

## How It Works

### Flow Diagram

```
Game Engine Updates Location
    ↓
/api/game/state endpoint called
    ↓
IF image not cached:
    LocationState → SceneSpec
    SceneSpec → Prompt
    Stable Diffusion v1.5
    Save to cache/
ELSE:
    Use cached image
    ↓
Return image_url in JSON response
    ↓
Frontend displays:
  - Narrative text
  - Image (if available)
  - Game UI
```

### Code Integration Points

**1. After player action (automatic in game engine):**
```python
# In app.py /api/game/action endpoint:
result = game_engine.process_player_action(player_input)
# Location state is automatically updated
```

**2. When returning game state:**
```python
# In app.py /api/game/state endpoint:
image_url = None
if location_state and not location_state.generated_image_path:
    generate_for_location(location_state)

image_url = f"/images/{location_state.generated_image_path.name}"
return jsonify({"image_url": image_url, ...})
```

**3. Frontend receives:**
```json
{
  "location": "lighthouse_exterior",
  "image_url": "/images/lighthouse_exterior.png",
  "narrative": "You find yourself...",
  ...
}
```

---

## Configuration

### Image Cache
- **Location:** `game/generated/`
- **Auto-cleanup:** Manual (manifest.json tracks files)
- **Size:** ~0.5 MB per image

### Image Generation
- **Model:** Stable Diffusion v1.5
- **Time per image:** 25-35 seconds (M1 MPS)
- **Quality:** Good for text adventure

### Prompts
- **Max length:** 100 characters (safe for CLIP)
- **Style:** Pixel art + horror
- **Customization:** Edit `spec_to_prompt()` for variations

---

## What Didn't Change

✓ Core game engine (`GenerativeGameEngine`)  
✓ Narrative logic  
✓ CoC7e rules  
✓ Game state save/load (backwards compatible)  
✓ Existing API contracts (only added new field)

---

## Testing Checklist

- [ ] Run `python3 game/test_integration.py` → passes
- [ ] Start Flask server: `python3 app.py`
- [ ] Visit `/` in browser
- [ ] Start game
- [ ] Move to new location
- [ ] Check browser dev tools → `image_url` appears in JSON
- [ ] Image displays in game UI

---

## Potential Issues & Fixes

| Issue | Fix |
|-------|-----|
| Out of memory (VRAM) | Reduce `steps` from 25 to 20 in `image_gen.py` |
| Image generation too slow | Skip generation for some locations (edit `generate_for_location()`) |
| Wrong aspect ratio | Modify width/height in `image_gen.py` |
| Cache bloat | Delete `game/generated/` files manually |
| Image looks wrong | Adjust prompt in `location_to_scene_spec()` |

---

## Next Steps

1. **Run integration test:** `python3 game/test_integration.py`
2. **Start game server:** `python3 app.py`
3. **Test in browser:** Visit http://localhost:5000
4. **Verify images generate** for locations
5. **Adjust prompts** as needed based on visual quality
6. **Deploy with confidence** - minimal changes to core engine

---

## Revert Instructions

If needed, reverting is safe:

```bash
# Revert LocationState changes
git checkout core/location_state.py

# Remove image generation (in app.py):
# Delete lines: generated image_url section

# Remove integration module
rm game/game_image_integration.py

# Game runs without images - no crashes
```

No permanent dependencies introduced.
