#!/usr/bin/env python3
"""
Generate final test images with optimized prompts.
"""

import sys
from pathlib import Path
from scene_spec import EXAMPLE_SCENES, SceneSpec, LightingSpec, SceneObject
from art_director import spec_to_prompt, load_style_bible
from image_gen import LocalImageGenerator
from cache import ImageCache


# Enhanced scenes with better descriptions
ENHANCED_SCENES = {
    "lighthouse_exterior": SceneSpec(
        location_key="lighthouse_exterior",
        location_type="lighthouse_exterior",
        mood="eerie_quiet",
        lighting=LightingSpec(
            source="distant_moon",
            color="pale_gray",
            intensity="low"
        ),
        objects=[
            SceneObject("lighthouse_tower", "center_background"),
            SceneObject("rocky_shore", "center_foreground"),
            SceneObject("fog", "background"),
            SceneObject("waves", "foreground")
        ],
        palette=["storm_gray", "pale_blue", "dark_rock"],
        camera="wide_eye_level",
        danger_level=1,
        contamination=5
    ),

    "lighthouse_interior": SceneSpec(
        location_key="lighthouse_interior",
        location_type="lighthouse_interior",
        mood="oppressive_horror",
        lighting=LightingSpec(
            source="ceiling_beam",
            color="sickly_amber",
            intensity="moderate"
        ),
        objects=[
            SceneObject("spiral_stairs", "center"),
            SceneObject("iron_railing", "left"),
            SceneObject("stone_walls", "background"),
            SceneObject("chains", "ceiling")
        ],
        palette=["rust_brown", "stone_gray", "amber"],
        camera="tall_chamber",
        danger_level=2,
        contamination=20
    ),

    "ritual_chamber": SceneSpec(
        location_key="ritual_chamber",
        location_type="ritual_chamber",
        mood="cosmic_scale",
        lighting=LightingSpec(
            source="unnatural_glow",
            color="sickly_purple",
            intensity="unnatural"
        ),
        objects=[
            SceneObject("altar", "center_background"),
            SceneObject("ancient_symbols", "walls"),
            SceneObject("carved_stone", "floor"),
            SceneObject("glowing_runes", "ceiling")
        ],
        palette=["deep_purple", "stone_gray", "violet_glow"],
        camera="wide_eye_level",
        danger_level=4,
        contamination=60
    ),

    "keeper_quarters": SceneSpec(
        location_key="keeper_quarters",
        location_type="keeper_quarters",
        mood="creeping_dread",
        lighting=LightingSpec(
            source="oil_lamp",
            color="warm_orange",
            intensity="dim"
        ),
        objects=[
            SceneObject("writing_desk", "left_midground"),
            SceneObject("logbooks", "desk"),
            SceneObject("sparse_furniture", "background"),
            SceneObject("single_window", "wall")
        ],
        palette=["dark_wood", "paper_white", "lamp_orange"],
        camera="wide_eye_level",
        danger_level=2,
        contamination=30
    ),

    "sunken_chamber": SceneSpec(
        location_key="sunken_chamber",
        location_type="underground_cavern",
        mood="alien_wrongness",
        lighting=LightingSpec(
            source="bioluminescent",
            color="sickly_cyan",
            intensity="unnatural"
        ),
        objects=[
            SceneObject("wet_stone_walls", "background"),
            SceneObject("mineral_formations", "ceiling"),
            SceneObject("dark_water", "foreground"),
            SceneObject("strange_symbols", "walls")
        ],
        palette=["sickly_green", "deep_cyan", "black"],
        camera="wide_eye_level",
        danger_level=4,
        contamination=70
    ),
}


def main():
    print("\n" + "=" * 70)
    print("GENERATING FINAL TEST IMAGES")
    print("=" * 70)

    style_bible = load_style_bible()
    gen = LocalImageGenerator()
    cache = ImageCache("generated")

    results = []

    for scene_key, spec in ENHANCED_SCENES.items():
        print(f"\n📍 {scene_key.upper()}")
        print("-" * 70)

        # Generate prompt
        prompt, negative = spec_to_prompt(spec, style_bible)

        print(f"Mood: {spec.mood}")
        print(f"Danger: {spec.danger_level}/5 | Contamination: {spec.contamination}%")
        print(f"Prompt: {prompt[:100]}...")
        print(f"Negative: {negative[:80]}...")

        # Generate
        output_path = f"generated/{scene_key}_test.png"
        try:
            path = gen.generate(
                prompt=prompt,
                negative_prompt=negative,
                output_path=output_path,
                steps=30,
                seed=hash(scene_key) % (2**31)
            )

            cache.cache_image(spec, path, prompt, negative)

            from pathlib import Path as P
            size = P(path).stat().st_size / (1024 * 1024)
            print(f"\n✓ Generated: {path} ({size:.2f} MB)")
            results.append((scene_key, "✓", output_path))

        except Exception as e:
            print(f"\n✗ Failed: {e}")
            results.append((scene_key, "✗", str(e)))

    # Summary
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    for scene_key, status, info in results:
        symbol = "✓" if status == "✓" else "✗"
        print(f"{symbol} {scene_key:25} {info}")

    passed = sum(1 for _, s, _ in results if s == "✓")
    total = len(results)

    print(f"\n{passed}/{total} scenes generated")
    print(f"\nAll images saved to: generated/")
    print("Review them and provide feedback:")
    print("  - Which look good?")
    print("  - Which need adjustment?")
    print("  - Any prompts to refine?")


if __name__ == "__main__":
    main()
