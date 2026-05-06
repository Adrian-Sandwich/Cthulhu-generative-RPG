#!/usr/bin/env python3
"""
Batch Image Refinement using VQGAN+CLIP
Refines all generated images with consistent style and enhanced details
"""

import os
from pathlib import Path
from PIL import Image
from .vqgan_refiner import VQGANClipRefiner
from .batch_generator import TEST_SCENARIOS


def refine_batch_images():
    """Refine all batch images using CLIP embeddings and style grading"""

    print("\n" + "=" * 80)
    print("VQGAN+CLIP IMAGE REFINEMENT - Lovecraftian Batch")
    print("=" * 80 + "\n")

    # Initialize refiner
    refiner = VQGANClipRefiner(model_name="ViT-B-32", pretrained="openai")

    # Directories
    input_dir = Path("graphics_engine/data/batch_images")
    output_dir = Path("graphics_engine/data/refined_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Map scenarios to image files
    refined_count = 0
    failed_count = 0

    print(f"📊 Refining {len(TEST_SCENARIOS)} images with CLIP-guided enhancement...\n")

    for idx, (location, seed, description) in enumerate(TEST_SCENARIOS, 1):
        try:
            # Find matching image file
            filename = f"batch_{idx:03d}_{location.replace(' ', '_').lower()}_s{seed}.png"
            input_path = input_dir / filename

            if not input_path.exists():
                print(f"[{idx:2d}/{len(TEST_SCENARIOS)}] ⚠️  {description}")
                print(f"           File not found: {filename}\n")
                failed_count += 1
                continue

            # Load image
            img = Image.open(input_path)

            # Analyze with CLIP
            print(f"[{idx:2d}/{len(TEST_SCENARIOS)}] 🎨 {description}")
            analysis = refiner.analyze_image(img, location)
            print(f"           Primary match: {analysis['primary_score']:.3f}")
            print(f"           Style match: {analysis['style_score']:.3f}")

            # Refine image
            refined_img = refiner.refine(img, location, apply_all=True)

            # Get AI-generated description
            ai_description = refiner.get_description(refined_img, location)
            print(f"           AI Description: {ai_description}")

            # Save refined image
            output_filename = f"refined_{idx:03d}_{location.replace(' ', '_').lower()}_s{seed}.png"
            output_path = output_dir / output_filename

            refined_img.save(output_path, format="PNG")
            file_size_kb = output_path.stat().st_size / 1024

            print(f"           ✓ Saved: {output_filename} ({file_size_kb:.0f} KB)")
            print()

            refined_count += 1

        except Exception as e:
            print(f"[{idx:2d}/{len(TEST_SCENARIOS)}] ✗ Error: {str(e)[:60]}")
            print()
            failed_count += 1

    # Summary
    print("\n" + "=" * 80)
    print(f"✅ Refinement Complete")
    print("=" * 80)
    print(f"\n📊 Results:")
    print(f"   Refined: {refined_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total: {refined_count + failed_count}")
    print(f"\n📁 All refined images saved to: {output_dir}\n")

    # List refined files
    print("Refined files:")
    for i, filepath in enumerate(sorted(output_dir.glob("*.png")), 1):
        size_kb = filepath.stat().st_size / 1024
        print(f"  {i:2d}. {filepath.name} ({size_kb:.0f} KB)")

    print()


if __name__ == "__main__":
    refine_batch_images()
