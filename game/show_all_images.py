#!/usr/bin/env python3
# Standalone experiment script — nothing in the app imports it (fan-in 0).
# Scope: image-generation experiments. See docs/TECH_DEBT.md ("Dead
# standalone scripts"). Delete once the image-gen experiments conclude.
"""
Display all generated test images for review.
"""

from pathlib import Path
import json


def main():
    gen_dir = Path("generated")

    print("\n" + "=" * 70)
    print("GENERATED IMAGES FOR REVIEW")
    print("=" * 70)

    # Find all test images
    test_images = sorted(gen_dir.glob("*_test.png"))

    if not test_images:
        print("\n❌ No test images found in generated/")
        print("Run: python3 generate_final_test.py")
        return

    print(f"\n✓ Found {len(test_images)} images:\n")

    for i, img_path in enumerate(test_images, 1):
        size_mb = img_path.stat().st_size / (1024 * 1024)
        scene_name = img_path.stem.replace("_test", "")

        print(f"{i}. {scene_name}")
        print(f"   Path: {img_path}")
        print(f"   Size: {size_mb:.2f} MB")
        print()

    print("=" * 70)
    print("TO REVIEW:")
    print("=" * 70)
    print("\n1. Open images:")
    print("   open generated/*_test.png")
    print("\n2. Use EVALUATION_TEMPLATE.md to rate each")
    print("\n3. Share feedback:")
    print("   - Which look good?")
    print("   - Which need adjustment?")
    print("   - Any prompts to change?")

    # Show cache status
    print("\n" + "=" * 70)
    print("CACHE STATUS")
    print("=" * 70)

    manifest_file = gen_dir / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file) as f:
            manifest = json.load(f)
        print(f"\nCached images: {len(manifest)}")
        for hash_key, entry in list(manifest.items())[:5]:
            print(f"  - {entry.get('location_key', 'unknown')}")
        if len(manifest) > 5:
            print(f"  ... and {len(manifest) - 5} more")


if __name__ == "__main__":
    main()
