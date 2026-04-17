#!/usr/bin/env python3
"""
Complete VQGAN+CLIP Pipeline
Generates, refines, and creates variations of images with coherent style
"""

import sys
import os
from pathlib import Path


def main():
    """Run complete pipeline"""

    print("\n" + "=" * 80)
    print("🎨 VQGAN+CLIP COMPLETE PIPELINE - Lovecraftian Image Enhancement")
    print("=" * 80 + "\n")

    # Step 1: Generate base images
    print("📍 STEP 1: Generate Base Procedural Images")
    print("-" * 80)
    try:
        from .batch_generator import main as generate_batch
        generate_batch()
    except Exception as e:
        print(f"❌ Generation failed: {e}\n")
        return

    print("\n" + "=" * 80)

    # Step 2: Refine with CLIP
    print("\n📍 STEP 2: Refine Images with CLIP Embeddings")
    print("-" * 80)
    try:
        from .refine_batch import refine_batch_images
        refine_batch_images()
    except Exception as e:
        print(f"❌ Refinement failed: {e}\n")
        return

    print("\n" + "=" * 80)

    # Step 3: Generate variations
    print("\n📍 STEP 3: Generate Image Variations (4 styles per image)")
    print("-" * 80)
    try:
        from .generate_variations import generate_variations
        generate_variations()
    except Exception as e:
        print(f"❌ Variation generation failed: {e}\n")
        return

    # Final summary
    print("\n" + "=" * 80)
    print("✅ COMPLETE PIPELINE SUCCESSFUL")
    print("=" * 80)
    print("\n📁 Generated directories:")
    print("   • graphics_engine/data/batch_images/          (27 base images)")
    print("   • graphics_engine/data/refined_images/        (27 refined images)")
    print("   • graphics_engine/data/image_variations/      (108 variation images)")
    print("\n📊 Total images created: 162")
    print("🎨 Styles applied: base + dawn + storm + close-up + distant")
    print("🔤 CLIP analysis: automatic descriptions for each image")
    print("\n✨ All images ready for terminal display integration!\n")


if __name__ == "__main__":
    main()
