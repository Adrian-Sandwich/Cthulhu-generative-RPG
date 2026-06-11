#!/usr/bin/env python3
"""
Test the complete integration: LocationState → Image Generation
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.location_state import LocationState
from game_image_integration import generate_for_location


def test_integration():
    """Test image generation for a location."""

    print("\n" + "=" * 70)
    print("INTEGRATION TEST: LocationState → Image Generation")
    print("=" * 70)

    # Create a test location
    location = LocationState(
        key="lighthouse_exterior",
        name="Remote Lighthouse",
        base_description="A lone lighthouse stands on the rocky Maine coast, fog rolling in.",
        danger_level=1,
        contamination=10
    )

    print(f"\n📍 Location: {location.name}")
    print(f"   Key: {location.key}")
    print(f"   Danger: {location.danger_level}/5")
    print(f"   Contamination: {location.contamination}%")

    # Generate image
    print(f"\n🎨 Generating image...")
    image_path = generate_for_location(location)

    if image_path:
        print(f"✓ Success: {image_path}")
        print(f"   Size: {Path(image_path).stat().st_size / (1024 * 1024):.2f} MB")
        print(f"   Cached: {location.generated_image_path}")
        return True
    else:
        print(f"✗ Failed to generate image")
        return False


def test_cache():
    """Test that second call uses cache."""

    print("\n" + "=" * 70)
    print("CACHE TEST: Second call should use cache")
    print("=" * 70)

    location = LocationState(
        key="lighthouse_interior",
        name="Lighthouse Interior",
        base_description="Inside the lighthouse, spiral stairs ascending into darkness.",
        danger_level=2,
        contamination=30
    )

    print(f"\n📍 Location: {location.name}")

    # First call
    print(f"\n1️⃣ First call (generate)...")
    image1 = generate_for_location(location)

    # Second call
    print(f"\n2️⃣ Second call (should cache)...")
    location2 = LocationState(
        key="lighthouse_interior",
        name="Lighthouse Interior",
        base_description="Inside the lighthouse, spiral stairs ascending into darkness.",
        danger_level=2,
        contamination=30
    )
    image2 = generate_for_location(location2)

    if image1 and image2 and image1 == image2:
        print(f"✓ Cache working: {image1}")
        return True
    else:
        print(f"✗ Cache test failed")
        return False


if __name__ == "__main__":
    try:
        test1 = test_integration()
        test2 = test_cache()

        print("\n" + "=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print(f"Integration: {'✓ PASS' if test1 else '✗ FAIL'}")
        print(f"Cache: {'✓ PASS' if test2 else '✗ FAIL'}")

        if test1 and test2:
            print("\n✓ All integration tests passed!")
            sys.exit(0)
        else:
            print("\n✗ Some tests failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
