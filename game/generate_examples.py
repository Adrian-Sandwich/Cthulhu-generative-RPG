#!/usr/bin/env python3
"""
Generate example images for all test scenes.
Review visual quality and adjust prompts as needed.
"""

import sys
from pathlib import Path
from scene_spec import EXAMPLE_SCENES
from art_director import spec_to_prompt, load_style_bible
from image_gen import LocalImageGenerator
from cache import ImageCache


def main():
    print("\n" + "=" * 70)
    print("GENERATING EXAMPLE SCENES")
    print("=" * 70)

    style_bible = load_style_bible()
    gen = LocalImageGenerator()
    cache = ImageCache("generated")

    results = []

    for scene_key, spec in EXAMPLE_SCENES.items():
        print(f"\n📍 {scene_key.upper()}")
        print("-" * 70)

        # Generate prompt
        prompt, negative = spec_to_prompt(spec, style_bible)

        print(f"Mood: {spec.mood}")
        print(f"Danger: {spec.danger_level}/5 | Contamination: {spec.contamination}%")
        print(f"\nPrompt ({len(prompt)} chars):")
        print(f"  {prompt[:120]}...")
        print(f"\nNegative ({len(negative)} chars):")
        print(f"  {negative[:100]}...")

        # Generate
        output_path = f"generated/{scene_key}.png"
        try:
            gen.generate(
                prompt=prompt,
                negative_prompt=negative,
                output_path=output_path,
                steps=30,
                seed=hash(scene_key) % (2**31)  # Reproducible seed
            )

            # Cache it
            cache.cache_image(spec, output_path, prompt, negative)

            size = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"\n✓ Generated: {output_path} ({size:.2f} MB)")
            results.append((scene_key, "✓", output_path))

        except Exception as e:
            print(f"\n✗ Failed: {e}")
            results.append((scene_key, "✗", str(e)))

    # Summary
    print("\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)

    for scene_key, status, info in results:
        symbol = "✓" if status == "✓" else "✗"
        print(f"{symbol} {scene_key:30} {info}")

    passed = sum(1 for _, s, _ in results if s == "✓")
    total = len(results)

    print(f"\n{passed}/{total} scenes generated successfully")
    print(f"\n📁 Check: ./generated/")
    print("   Review images and evaluate:")
    print("   - Visual coherence with description")
    print("   - Horror/Lovecraftian aesthetic")
    print("   - Pixel art style consistency")
    print("   - First-person perspective clarity")
    print("   - Playability (readable as game background)")


if __name__ == "__main__":
    main()
