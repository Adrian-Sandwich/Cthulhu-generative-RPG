#!/usr/bin/env python3
"""
End-to-end test: SceneSpec → Prompt → Image Generation → Cache
Standalone test to validate pipeline before integrating with game engine.
"""

import sys
from pathlib import Path

# Local imports
from scene_spec import EXAMPLE_SCENES, SceneSpec, LightingSpec, SceneObject
from art_director import spec_to_prompt, load_style_bible
from image_gen import LocalImageGenerator, estimate_generation_time
from cache import ImageCache


def test_scene_spec():
    """Test 1: Verify SceneSpec can be created and serialized."""
    print("\n" + "=" * 70)
    print("TEST 1: SceneSpec Creation & Serialization")
    print("=" * 70)

    for key, spec in EXAMPLE_SCENES.items():
        print(f"\n✓ {key}")
        print(f"  Location: {spec.location_type}")
        print(f"  Mood: {spec.mood}")
        print(f"  Contamination: {spec.contamination}")
        print(f"  Objects: {len(spec.objects)}")

    return True


def test_prompt_generation():
    """Test 2: Verify SceneSpec → Prompt conversion."""
    print("\n" + "=" * 70)
    print("TEST 2: Prompt Generation")
    print("=" * 70)

    style_bible = load_style_bible()

    for key, spec in EXAMPLE_SCENES.items():
        prompt, negative = spec_to_prompt(spec, style_bible)

        print(f"\n{key}:")
        print(f"  Prompt length: {len(prompt)} chars")
        print(f"  Negative length: {len(negative)} chars")
        print(f"  Prompt preview: {prompt[:100]}...")

    return True


def test_cache_logic():
    """Test 3: Verify cache hashing and management."""
    print("\n" + "=" * 70)
    print("TEST 3: Cache Management")
    print("=" * 70)

    cache = ImageCache("test_generated")

    for key, spec in EXAMPLE_SCENES.items():
        spec_hash = cache._hash_spec(spec)
        print(f"\n{key}:")
        print(f"  Hash: {spec_hash}")
        print(f"  Cache key: {spec.location_key}_{spec.danger_level}_{spec.contamination}")

    print(f"\n✓ Cache directory: test_generated/")
    return True


def test_image_generation():
    """Test 4: Actually generate an image (requires GPU/CPU)."""
    print("\n" + "=" * 70)
    print("TEST 4: Image Generation")
    print("=" * 70)

    try:
        gen = LocalImageGenerator()
        print(f"✓ Generator initialized on {gen.device}")
        print(f"  Data type: {gen.dtype}")
        print(f"  Estimated time: {estimate_generation_time(gen.device, steps=20)}")

        # Use smallest scene for speed
        spec = EXAMPLE_SCENES["lighthouse_exterior"]
        style_bible = load_style_bible()
        prompt, negative = spec_to_prompt(spec, style_bible)

        print(f"\n✓ Using scene: {spec.location_key}")
        print(f"  Prompt: {prompt[:80]}...")

        # Generate image
        output_path = gen.generate(
            prompt=prompt,
            negative_prompt=negative,
            output_path="test_generated/test_output.png",
            width=640,
            height=480,
            steps=20,  # Reduced for testing
            seed=42  # Reproducible for testing
        )

        print(f"✓ Image generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"✗ Image generation failed: {e}")
        print(f"  Make sure you have:")
        print(f"    pip install diffusers transformers torch pillow")
        return None


def test_cache_integration():
    """Test 5: Cache an image and retrieve it."""
    print("\n" + "=" * 70)
    print("TEST 5: Cache Integration")
    print("=" * 70)

    cache = ImageCache("test_generated")
    spec = EXAMPLE_SCENES["lighthouse_interior"]
    style_bible = load_style_bible()
    prompt, negative = spec_to_prompt(spec, style_bible)

    # Simulate image path (doesn't need to exist for this test)
    fake_image_path = "test_generated/cached_image.png"

    cache.cache_image(spec, fake_image_path, prompt, negative)
    print(f"✓ Cached: {spec.location_key}")

    cached = cache.get_cached_path(spec)
    if cached:
        print(f"✓ Retrieved from cache: {cached}")
        return True
    else:
        print(f"✗ Failed to retrieve from cache")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║ POINT BLACK LIGHTHOUSE - IMAGE GENERATION PIPELINE TEST" + " " * 8 + "║")
    print("╚" + "=" * 68 + "╝")

    tests = [
        ("SceneSpec Creation", test_scene_spec),
        ("Prompt Generation", test_prompt_generation),
        ("Cache Logic", test_cache_logic),
        ("Image Generation", test_image_generation),
        ("Cache Integration", test_cache_integration),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"\n✗ {name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, "ERROR"))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for name, status in results:
        symbol = "✓" if status == "PASS" else "✗" if status == "ERROR" else "!"
        print(f"{symbol} {name}: {status}")

    passed = sum(1 for _, s in results if s == "PASS")
    total = len(results)

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Pipeline is viable.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
