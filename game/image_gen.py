#!/usr/bin/env python3
"""
Local image generation using Stable Diffusion.
Supports GPU (CUDA/MPS) and CPU fallback.
"""

import torch
from pathlib import Path
from typing import Optional
import warnings

warnings.filterwarnings("ignore")


class LocalImageGenerator:
    """Generates images using local Stable Diffusion model."""

    def __init__(self, model_id: str = "runwayml/stable-diffusion-v1-5"):
        """
        Initialize image generator with model selection.

        Args:
            model_id: HuggingFace model ID (default: runwayml/stable-diffusion-v1-5)

        Tested models:
            - runwayml/stable-diffusion-v1-5 (6GB VRAM, fast)
            - stabilityai/stable-diffusion-2-base (5GB VRAM, slightly better quality)
            - stabilityai/stable-diffusion-2.1 (5GB VRAM, best quality but slower)
        """

        # Detect device
        if torch.cuda.is_available():
            self.device = "cuda"
            self.device_name = torch.cuda.get_device_name(0)
            print(f"✓ CUDA GPU detected: {self.device_name}")
        elif torch.backends.mps.is_available():
            self.device = "mps"
            print("✓ Apple Metal GPU (MPS) detected")
        else:
            self.device = "cpu"
            print("⚠ No GPU detected, using CPU (slow)")

        # Set dtype based on device
        # Note: MPS has issues with float16, always use float32
        if self.device in ("cpu", "mps"):
            self.dtype = torch.float32
        else:
            self.dtype = torch.float16

        print(f"Loading {model_id.split('/')[-1]} on {self.device}...")

        try:
            from diffusers import StableDiffusionPipeline

            self.pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=self.dtype,
                safety_checker=None,  # Disable safety checker for horror content
            )
            self.pipe = self.pipe.to(self.device)
            self.pipe.enable_attention_slicing()  # Save memory

            print(f"✓ Model loaded successfully")

        except ImportError:
            print("ERROR: diffusers not installed")
            print("Install with: pip install diffusers transformers torch")
            raise

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        output_path: str = "output.png",
        width: int = 640,
        height: int = 480,
        steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
    ) -> str:
        """
        Generate an image from prompt.

        Args:
            prompt: Positive prompt
            negative_prompt: Things to avoid
            output_path: Where to save (relative or absolute)
            width: Image width (must be multiple of 8)
            height: Image height (must be multiple of 8)
            steps: Diffusion steps (30 default, 50+ for quality)
            guidance_scale: How strictly to follow prompt (7.5 default)
            seed: Random seed for reproducibility

        Returns:
            Path to saved image
        """

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure dimensions are valid
        width = (width // 8) * 8
        height = (height // 8) * 8

        print(f"\n{'=' * 70}")
        print(f"Generating {width}x{height} image...")
        print(f"Device: {self.device}")
        print(f"Steps: {steps}, Guidance: {guidance_scale}")
        print(f"Output: {output_path}")
        print(f"{'=' * 70}")

        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            generator = torch.Generator(device=self.device).manual_seed(
                torch.seed() % (2**32 - 1)
            )

        with torch.no_grad():
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                height=height,
                width=width,
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )

        image = result.images[0]
        image.save(str(output_path))

        print(f"✓ Image saved to {output_path}\n")
        return str(output_path)


def estimate_generation_time(device: str, steps: int = 30) -> str:
    """Rough estimate of generation time."""
    times = {
        "cuda": steps * 0.5,  # ~15s for 30 steps on RTX 3080
        "mps": steps * 3,     # ~90s for 30 steps on M1
        "cpu": steps * 20     # ~600s for 30 steps on CPU
    }
    seconds = times.get(device, steps * 20)
    minutes = seconds / 60
    return f"~{minutes:.1f} minutes"


if __name__ == "__main__":
    # Test
    gen = LocalImageGenerator()

    test_prompt = (
        "Retro pixel-art horror game background. Decaying stone chamber with moss. "
        "Sickly green ceiling glow, wet stone floor, broken columns. "
        "First-person perspective, 4:3 aspect ratio, oppressive atmosphere, "
        "no characters no UI no text."
    )

    test_negative = (
        "modern objects, photorealism, people, text overlays, bright colors, "
        "cartoon style, contemporary technology"
    )

    print(f"\nEstimated generation time: {estimate_generation_time(gen.device)}")

    gen.generate(
        prompt=test_prompt,
        negative_prompt=test_negative,
        output_path="/tmp/test_chamber.png",
        steps=20,
        seed=42
    )
