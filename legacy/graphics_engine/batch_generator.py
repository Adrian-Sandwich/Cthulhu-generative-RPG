#!/usr/bin/env python3
"""
Batch Image Generator - Generate multiple images for testing
Creates a variety of procedural images for different locations and seeds
"""

import os
from pathlib import Path
from .image.generator import ProceduralImageGenerator
from io import BytesIO


# Test scenarios: (location, seed, description)
TEST_SCENARIOS = [
    # Lighthouse - different times/conditions
    ("Lighthouse Exterior", 12345, "Lighthouse - Foggy arrival"),
    ("Lighthouse Exterior", 54321, "Lighthouse - Clear night"),
    ("Lighthouse Exterior", 99999, "Lighthouse - Storm approaching"),
    ("Lighthouse Exterior", 11111, "Lighthouse - Dawn"),
    ("Lighthouse Exterior", 22222, "Lighthouse - Dusk"),

    # Lighthouse Interior - various rooms
    ("Lighthouse Interior", 12345, "Lighthouse Interior - Main room"),
    ("Lighthouse Interior", 54321, "Lighthouse Interior - Spiral stairs"),
    ("Lighthouse Interior", 77777, "Lighthouse Interior - Top room"),
    ("Lighthouse Interior", 88888, "Lighthouse Interior - Keeper's quarters"),

    # Forest/Nature
    ("Forest", 12345, "Forest - Deep woods"),
    ("Forest", 54321, "Forest - Moonlit clearing"),
    ("Forest", 33333, "Forest - Ancient trees"),
    ("Forest", 44444, "Forest - Overgrown path"),

    # Crypt/Underground
    ("Crypt", 12345, "Crypt - Main chamber"),
    ("Crypt", 54321, "Crypt - Tomb passage"),
    ("Crypt", 55555, "Crypt - Deep crypts"),
    ("Crypt", 66666, "Crypt - Sealed chamber"),

    # Sea/Water
    ("Sea", 12345, "Sea - Rocky shore"),
    ("Sea", 54321, "Sea - Calm waters"),
    ("Sea", 77777, "Sea - Stormy seas"),
    ("Sea", 88888, "Sea - Shipwreck"),

    # Generic locations
    ("Beach", 12345, "Beach - Sandy coast"),
    ("Beach", 54321, "Beach - Isolated shore"),
    ("Cave", 12345, "Cave - Stone cavern"),
    ("Cave", 54321, "Cave - Underground river"),
    ("Village", 12345, "Village - Empty streets"),
    ("Village", 54321, "Village - Abandoned houses"),
]


def main():
    """Generate batch of images"""

    print("\n" + "="*80)
    print("BATCH IMAGE GENERATOR - Procedural Lighthouse Adventure")
    print("="*80 + "\n")

    # Setup
    output_dir = Path("graphics_engine/data/batch_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = ProceduralImageGenerator(width=640, height=480)

    print(f"📁 Output directory: {output_dir}\n")
    print(f"🎨 Generating {len(TEST_SCENARIOS)} images...\n")

    successful = 0
    failed = 0

    for idx, (location, seed, description) in enumerate(TEST_SCENARIOS, 1):
        try:
            print(f"[{idx:2d}/{len(TEST_SCENARIOS)}] {description}")

            # Generate image
            pil_image = generator.generate(location=location, seed=seed)

            # Save as PNG
            filename = f"batch_{idx:03d}_{location.replace(' ', '_').lower()}_s{seed}.png"
            filepath = output_dir / filename

            pil_image.save(filepath, format='PNG')

            # Get file size
            size_kb = filepath.stat().st_size / 1024

            print(f"           ✓ Saved: {filename} ({size_kb:.0f} KB)")

            successful += 1

        except Exception as e:
            print(f"           ✗ Error: {str(e)[:60]}")
            failed += 1

        print()

    # Summary
    print("\n" + "="*80)
    print(f"✅ Batch Generation Complete")
    print("="*80)
    print(f"\n📊 Results:")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total: {successful + failed}")
    print(f"\n📁 All images saved to: {output_dir}\n")

    # List generated files
    print("Generated files:")
    for i, filepath in enumerate(sorted(output_dir.glob("*.png")), 1):
        size_kb = filepath.stat().st_size / 1024
        print(f"  {i:2d}. {filepath.name} ({size_kb:.0f} KB)")

    print()


if __name__ == "__main__":
    main()
