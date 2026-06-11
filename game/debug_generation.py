#!/usr/bin/env python3
"""
Debug script to test image generation with different prompts and settings.
"""

from image_gen import LocalImageGenerator

def test_simple_prompt():
    """Test with a simpler, shorter prompt."""
    gen = LocalImageGenerator()

    # Simpler, shorter prompt
    prompts = [
        # Very basic
        (
            "Pixel art horror game background. Dark stone chamber. First-person view. 4:3 ratio.",
            "modern objects, people, text"
        ),
        # Medium
        (
            "Retro pixel-art horror. Decaying stone chamber with moss and wet floor. Sickly green light from above. "
            "First-person perspective, 4:3 ratio. Dark oppressive atmosphere.",
            "photorealism, people, cartoon"
        ),
        # Full detail
        (
            "Retro pixel-art horror game background. Ancient decaying stone chamber with cracked walls and creeping moss. "
            "Wet stone floor with broken columns. Sickly green-cyan ceiling glow casting strange shadows. "
            "First-person perspective, wide eye level camera, 4:3 aspect ratio. "
            "Dark oppressive oppressive atmosphere. Game asset quality. "
            "No characters, no UI, no text overlays. Playable background.",
            "modern objects, photorealism, people, text overlays, cartoon, bright colors"
        )
    ]

    for i, (positive, negative) in enumerate(prompts, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: Prompt length {len(positive)} chars")
        print(f"{'='*70}")
        print(f"Positive: {positive[:100]}...")
        print(f"Negative: {negative[:100]}...")

        try:
            path = gen.generate(
                prompt=positive,
                negative_prompt=negative,
                output_path=f"test_generated/debug_{i}.png",
                width=640,
                height=480,
                steps=30,
                guidance_scale=7.5,
                seed=42 + i
            )
            print(f"✓ Generated: {path}")

        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_simple_prompt()
