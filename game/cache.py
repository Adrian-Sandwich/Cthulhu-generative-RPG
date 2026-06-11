#!/usr/bin/env python3
"""
Image cache management.
Stores generated images and metadata to avoid regeneration.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Callable
from game.scene_spec import SceneSpec


class ImageCache:
    """Manages cached images and their scene specifications."""

    def __init__(self, cache_dir: str = "generated"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.manifest_file = self.cache_dir / "manifest.json"
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict:
        """Load cache index."""
        if self.manifest_file.exists():
            with open(self.manifest_file) as f:
                return json.load(f)
        return {}

    def _save_manifest(self):
        """Save cache index."""
        with open(self.manifest_file, "w") as f:
            json.dump(self.manifest, f, indent=2)

    def _hash_spec(self, spec: SceneSpec) -> str:
        """Generate hash from scene spec for caching."""
        # Use location_key + danger_level + contamination as cache key
        # This ensures revisiting same location with changed state uses new image
        key_str = f"{spec.location_key}_{spec.danger_level}_{spec.contamination}"
        return hashlib.md5(key_str.encode()).hexdigest()[:12]

    def get_cached_path(self, spec: SceneSpec) -> Optional[str]:
        """Return cached image path if it exists."""
        spec_hash = self._hash_spec(spec)

        if spec_hash in self.manifest:
            cached_path = self.manifest[spec_hash]["image_path"]
            if Path(cached_path).exists():
                return cached_path
            else:
                # Cache entry exists but file is gone, remove entry
                del self.manifest[spec_hash]
                self._save_manifest()

        return None

    def cache_image(
        self,
        spec: SceneSpec,
        image_path: str,
        prompt: str,
        negative_prompt: str
    ) -> str:
        """
        Register generated image in cache.

        Args:
            spec: SceneSpec that was used
            image_path: Path to generated image
            prompt: Positive prompt used
            negative_prompt: Negative prompt used

        Returns:
            Canonical cached image path
        """

        spec_hash = self._hash_spec(spec)
        image_path = str(Path(image_path).resolve())

        self.manifest[spec_hash] = {
            "location_key": spec.location_key,
            "danger_level": spec.danger_level,
            "contamination": spec.contamination,
            "image_path": image_path,
            "prompt": prompt[:200],  # Store abbreviated prompt
            "negative_prompt": negative_prompt[:200]
        }

        self._save_manifest()
        return image_path

    def get_or_generate(
        self,
        spec: SceneSpec,
        prompt: str,
        negative_prompt: str,
        gen_func: Callable[[str], str]
    ) -> str:
        """
        Get cached image or generate new one.

        Args:
            spec: Scene specification
            prompt: Positive prompt
            negative_prompt: Negative prompt
            gen_func: Generator function that takes output_path and returns path

        Returns:
            Path to image (cached or newly generated)
        """

        # Check cache
        cached = self.get_cached_path(spec)
        if cached:
            print(f"✓ Using cached image: {cached}")
            return cached

        # Generate new
        spec_hash = self._hash_spec(spec)
        output_path = self.cache_dir / f"scene_{spec_hash}.png"

        print(f"Generating new image: {output_path}")
        gen_func(str(output_path))

        # Cache it
        self.cache_image(spec, str(output_path), prompt, negative_prompt)
        return str(output_path)

    def clear_cache(self):
        """Delete all cached images (but keep manifest for history)."""
        for entry in self.manifest.values():
            path = Path(entry["image_path"])
            if path.exists():
                path.unlink()
        print("✓ Cache cleared")

    def list_cached(self) -> list:
        """List all cached scenes."""
        return list(self.manifest.values())

    def get_cache_size(self) -> tuple[int, float]:
        """Return (file count, size in MB)."""
        count = 0
        size = 0

        for entry in self.manifest.values():
            path = Path(entry["image_path"])
            if path.exists():
                count += 1
                size += path.stat().st_size

        return count, size / (1024 * 1024)


if __name__ == "__main__":
    # Test
    from scene_spec import EXAMPLE_SCENES

    cache = ImageCache("test_cache")

    for key, spec in EXAMPLE_SCENES.items():
        print(f"Spec hash: {cache._hash_spec(spec)}")

    print(f"\nCache contents:")
    for item in cache.list_cached():
        print(f"  {item['location_key']}: {item['image_path']}")

    count, size_mb = cache.get_cache_size()
    print(f"\nCache: {count} images, {size_mb:.1f} MB")
