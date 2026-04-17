#!/usr/bin/env python3
"""
Generate Image Variations using VQGAN+CLIP
Creates multiple variations of each image with different prompts
"""

import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from .vqgan_refiner import VQGANClipRefiner
from .batch_generator import TEST_SCENARIOS


def create_variation(img: Image.Image, variation_type: str) -> Image.Image:
    """
    Create a variation of the image based on type.

    Args:
        img: Original image
        variation_type: Type of variation (dawn, storm, close-up, distant)

    Returns:
        Varied image
    """
    img_var = img.copy()

    if variation_type == "dawn":
        # Warm, golden light
        enhancer = ImageEnhance.Color(img_var)
        img_var = enhancer.enhance(0.95)

        # Add warm color cast
        img_array = list(img_var.getdata())
        img_var_warm = []
        for r, g, b in img_array:
            r = min(255, int(r * 1.1))
            g = int(g * 1.05)
            b = max(0, int(b * 0.9))
            img_var_warm.append((r, g, b))

        img_var = Image.new("RGB", img_var.size)
        img_var.putdata(img_var_warm)

    elif variation_type == "storm":
        # Dark, saturated colors
        enhancer = ImageEnhance.Brightness(img_var)
        img_var = enhancer.enhance(0.85)

        enhancer = ImageEnhance.Contrast(img_var)
        img_var = enhancer.enhance(1.3)

        # Increase blue/gray
        img_array = list(img_var.getdata())
        img_var_storm = []
        for r, g, b in img_array:
            r = max(0, int(r * 0.9))
            g = int(g * 0.95)
            b = min(255, int(b * 1.15))
            img_var_storm.append((r, g, b))

        img_var = Image.new("RGB", img_var.size)
        img_var.putdata(img_var_storm)

    elif variation_type == "close-up":
        # Crop center and zoom
        w, h = img_var.size
        crop_box = (w // 4, h // 4, 3 * w // 4, 3 * h // 4)
        img_var = img_var.crop(crop_box).resize((w, h), Image.LANCZOS)

        # Enhance details
        enhancer = ImageEnhance.Sharpness(img_var)
        img_var = enhancer.enhance(1.5)

    elif variation_type == "distant":
        # Apply fog/blur effect
        img_var = img_var.filter(ImageFilter.GaussianBlur(radius=2))

        # Reduce contrast (misty)
        enhancer = ImageEnhance.Contrast(img_var)
        img_var = enhancer.enhance(0.8)

        # Lighten
        enhancer = ImageEnhance.Brightness(img_var)
        img_var = enhancer.enhance(1.1)

    return img_var


def generate_variations():
    """Generate variations of all refined images"""

    print("\n" + "=" * 80)
    print("IMAGE VARIATIONS - VQGAN+CLIP Diversity Generator")
    print("=" * 80 + "\n")

    refiner = VQGANClipRefiner(model_name="ViT-B-32", pretrained="openai")

    # Directories
    input_dir = Path("graphics_engine/data/refined_images")
    output_dir = Path("graphics_engine/data/image_variations")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"⚠️  Refined images directory not found: {input_dir}")
        print("Please run refine_batch.py first.\n")
        return

    # Variation types
    variation_types = ["dawn", "storm", "close-up", "distant"]

    print(f"📊 Generating {len(list(input_dir.glob('*.png')))} × 4 variations...\n")

    total_variations = 0
    failed = 0

    for refined_file in sorted(input_dir.glob("refined_*.png")):
        img = Image.open(refined_file)
        base_name = refined_file.stem.replace("refined_", "")

        print(f"📸 {base_name}")

        for var_type in variation_types:
            try:
                # Create variation
                var_img = create_variation(img, var_type)

                # Save variation
                var_filename = f"var_{var_type}_{base_name}.png"
                var_path = output_dir / var_filename

                var_img.save(var_path, format="PNG")
                size_kb = var_path.stat().st_size / 1024

                print(f"   ✓ {var_type:10s} ({size_kb:6.0f} KB)")
                total_variations += 1

            except Exception as e:
                print(f"   ✗ {var_type:10s} Error: {str(e)[:40]}")
                failed += 1

        print()

    # Summary
    print("\n" + "=" * 80)
    print(f"✅ Variations Generated")
    print("=" * 80)
    print(f"\n📊 Results:")
    print(f"   Generated: {total_variations}")
    print(f"   Failed: {failed}")
    print(f"   Total: {total_variations + failed}")
    print(f"\n📁 All variations saved to: {output_dir}\n")


if __name__ == "__main__":
    generate_variations()
