#!/usr/bin/env python3
"""
Integration layer between GenerativeGameEngine and image generation.
Handles scene-to-image pipeline without modifying core engine.
"""

from pathlib import Path
from typing import Optional
from core.location_state import LocationState
from game.scene_spec import SceneSpec
from game.art_director import spec_to_prompt, load_style_bible
from game.image_gen import LocalImageGenerator
from game.cache import ImageCache


class ImageGenerationService:
    """Service to generate and cache images for game locations."""

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = str(Path(__file__).parent / "generated")
        self.cache = ImageCache(cache_dir)
        self.style_bible = load_style_bible()
        self.generator = None  # Lazy load
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def _get_generator(self) -> LocalImageGenerator:
        """Lazy load image generator (expensive operation)."""
        if self.generator is None:
            print("[ImageGen] Initializing local image generator...")
            self.generator = LocalImageGenerator()
        return self.generator

    def location_to_scene_spec(self, location_state: LocationState) -> SceneSpec:
        """
        Convert LocationState to SceneSpec for image generation.
        This is where game state influences visual appearance.
        """

        # Map location names to scene types
        location_map = {
            "lighthouse_exterior": "lighthouse_exterior",
            "lighthouse_interior": "lighthouse_interior",
            "underground_chamber": "underground_cavern",
            "ritual_chamber": "ritual_chamber",
            "keeper_quarters": "keeper_quarters",
        }

        scene_type = location_map.get(location_state.key, "decaying_chamber")

        spec = SceneSpec(
            location_key=location_state.key,
            location_type=scene_type,
            mood="oppressive_horror",  # Default, can be customized
            lighting=None,  # Will be filled by spec_to_prompt
            objects=[],
            palette=[],
            camera="wide_eye_level",
            danger_level=min(5, location_state.danger_level + 1),  # Escalate visual danger
            contamination=location_state.contamination,
            forbidden=[]
        )

        return spec

    def generate_image_for_location(
        self,
        location_state: LocationState,
        verbose: bool = True
    ) -> Optional[str]:
        """
        Generate image for a location if not already cached.

        Args:
            location_state: Current location state from game
            verbose: Print progress

        Returns:
            Path to generated image, or None if generation failed
        """

        # Convert location to scene spec
        spec = self.location_to_scene_spec(location_state)

        # Check cache
        cached = self.cache.get_cached_path(spec)
        if cached:
            if verbose:
                print(f"[ImageGen] Using cached image: {cached}")
            location_state.generated_image_path = cached
            return cached

        # Generate new
        try:
            if verbose:
                print(f"[ImageGen] Generating image for {location_state.key}...")

            prompt, negative = spec_to_prompt(spec, self.style_bible)

            if verbose:
                print(f"[ImageGen] Prompt: {prompt[:80]}...")

            gen = self._get_generator()
            output_path = self.cache_dir / f"{location_state.key}.png"

            path = gen.generate(
                prompt=prompt,
                negative_prompt=negative,
                output_path=str(output_path),
                steps=25,
                seed=hash(location_state.key) % (2**31)  # Reproducible
            )

            # Cache it
            self.cache.cache_image(spec, path, prompt, negative)
            location_state.generated_image_path = path

            if verbose:
                print(f"[ImageGen] ✓ Image generated: {path}")

            return path

        except Exception as e:
            print(f"[ImageGen] ✗ Failed to generate image: {e}")
            return None


# Global instance (lazy loaded)
_image_service = None


def get_image_service() -> ImageGenerationService:
    """Get singleton image generation service."""
    global _image_service
    if _image_service is None:
        _image_service = ImageGenerationService()
    return _image_service


def generate_for_location(location_state: LocationState) -> Optional[str]:
    """
    Convenience function to generate image for a location.
    Call this from game engine after updating location state.
    """
    service = get_image_service()
    return service.generate_image_for_location(location_state, verbose=True)
