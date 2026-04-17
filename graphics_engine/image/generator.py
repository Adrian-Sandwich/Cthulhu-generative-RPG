#!/usr/bin/env python3
"""
Image Generator - Procedural image generation using Perlin noise
Generates 640x480 retro pixel art images for Lovecraftian horror
"""

from PIL import Image, ImageDraw
import random
from .palette import get_palette, interpolate_color


class ProceduralImageGenerator:
    """Generate pixel art images using Perlin noise and procedural rules"""

    def __init__(self, width: int = 640, height: int = 480):
        """
        Initialize image generator.

        Args:
            width: Image width in pixels
            height: Image height in pixels
        """
        self.width = width
        self.height = height

    def generate(self, location: str, seed: int = 0) -> Image.Image:
        """
        Generate a procedural image for a location.

        Args:
            location: Location name (e.g., "Lighthouse Exterior")
            seed: Random seed for reproducibility

        Returns:
            PIL Image object
        """
        random.seed(seed)

        # Get palette for location
        palette = get_palette(location)

        # Create base image
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        pixels = img.load()

        # Generate terrain using simple Perlin-like noise
        terrain = self._generate_terrain(seed)

        # Paint pixels
        for y in range(self.height):
            for x in range(self.width):
                # Get noise value at this position
                value = terrain[y][x]

                # Map to color
                color = interpolate_color(value, palette)

                # Add slight variation
                if random.random() < 0.1:  # 10% dithering
                    r, g, b = color
                    r = max(0, min(255, r + random.randint(-15, 15)))
                    g = max(0, min(255, g + random.randint(-15, 15)))
                    b = max(0, min(255, b + random.randint(-15, 15)))
                    color = (r, g, b)

                pixels[x, y] = color

        # Draw location-specific features
        self._draw_features(img, location, seed)

        return img

    def _generate_terrain(self, seed: int) -> list:
        """
        Generate Perlin-like noise terrain.

        Args:
            seed: Random seed

        Returns:
            2D list of values from 0.0 to 1.0
        """
        try:
            from perlin_noise import PerlinNoise
            noise = PerlinNoise(octaves=4, seed=seed)

            terrain = []
            for y in range(self.height):
                row = []
                for x in range(self.width):
                    # Scale coordinates for interesting features
                    nx = x / 100.0
                    ny = y / 100.0
                    value = noise([nx, ny])

                    # Normalize to 0-1
                    value = (value + 1.0) / 2.0
                    value = max(0.0, min(1.0, value))

                    row.append(value)
                terrain.append(row)

            return terrain

        except ImportError:
            # Fallback: simple gradient if perlin_noise not installed
            return self._generate_simple_gradient(seed)

    def _generate_simple_gradient(self, seed: int) -> list:
        """
        Generate simple gradient terrain (fallback when perlin_noise unavailable).

        Args:
            seed: Random seed

        Returns:
            2D list of values
        """
        random.seed(seed)

        # Create multiple octaves of randomness
        terrain = [[0.0 for _ in range(self.width)] for _ in range(self.height)]

        # Add noise at different scales
        for scale in [100, 50, 25]:
            for y in range(self.height):
                for x in range(self.width):
                    # Simple sine-based noise
                    nx = x / scale
                    ny = y / scale
                    import math
                    value = (math.sin(nx) + math.cos(ny)) / 2.0
                    value = (value + 1.0) / 2.0  # Normalize to 0-1
                    terrain[y][x] += value * (1.0 / 3.0)

        return terrain

    def _draw_features(self, img: Image.Image, location: str, seed: int):
        """
        Draw location-specific features (buildings, trees, etc).

        Args:
            img: PIL Image to draw on
            location: Location name
            seed: Random seed
        """
        random.seed(seed)
        draw = ImageDraw.Draw(img)

        location_lower = location.lower()

        if "lighthouse" in location_lower:
            self._draw_lighthouse(draw)
        elif "forest" in location_lower:
            self._draw_forest(draw)
        elif "crypt" in location_lower:
            self._draw_crypt(draw)
        elif "sea" in location_lower:
            self._draw_sea(draw)

    def _draw_lighthouse(self, draw: ImageDraw.ImageDraw):
        """Draw lighthouse structure"""
        # Main tower
        tower_x = self.width // 2
        tower_y = self.height // 2

        # Tower body
        tower_width = 80
        tower_height = 300
        draw.rectangle(
            [tower_x - tower_width//2, tower_y - tower_height//2,
             tower_x + tower_width//2, tower_y + tower_height//2],
            fill=(200, 200, 200),
            outline=(100, 100, 100)
        )

        # Tower stripes (weathering)
        for i in range(0, tower_height, 40):
            y = tower_y - tower_height//2 + i
            draw.line(
                [(tower_x - tower_width//2, y),
                 (tower_x + tower_width//2, y)],
                fill=(150, 150, 150),
                width=2
            )

        # Light room at top
        draw.ellipse(
            [tower_x - 50, tower_y - tower_height//2 - 30,
             tower_x + 50, tower_y - tower_height//2 + 30],
            fill=(80, 80, 80),
            outline=(50, 50, 50)
        )

        # Light beacon
        draw.ellipse(
            [tower_x - 20, tower_y - tower_height//2 - 10,
             tower_x + 20, tower_y - tower_height//2 + 10],
            fill=(255, 200, 100),
            outline=(200, 150, 50)
        )

        # Door
        draw.rectangle(
            [tower_x - 20, tower_y + tower_height//2 - 50,
             tower_x + 20, tower_y + tower_height//2],
            fill=(80, 60, 40),
            outline=(60, 40, 20)
        )

        # Cottage
        cottage_x = tower_x - 150
        cottage_y = tower_y + 100
        draw.rectangle(
            [cottage_x - 60, cottage_y - 40,
             cottage_x + 60, cottage_y + 40],
            fill=(180, 140, 100),
            outline=(100, 80, 60)
        )

        # Cottage roof
        draw.polygon(
            [(cottage_x - 70, cottage_y - 40),
             (cottage_x + 70, cottage_y - 40),
             (cottage_x, cottage_y - 80)],
            fill=(100, 60, 40),
            outline=(60, 40, 20)
        )

    def _draw_forest(self, draw: ImageDraw.ImageDraw):
        """Draw forest/trees"""
        random.seed(42)
        for _ in range(15):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)

            # Tree trunk
            draw.rectangle(
                [x - 15, y - 30, x + 15, y + 80],
                fill=(70, 50, 30)
            )

            # Tree foliage
            draw.polygon(
                [(x - 50, y), (x + 50, y), (x, y - 100)],
                fill=(34, 139, 34),
                outline=(20, 80, 20)
            )

    def _draw_crypt(self, draw: ImageDraw.ImageDraw):
        """Draw crypt/tomb structure"""
        # Stone walls
        for x in range(0, self.width, 100):
            draw.line([(x, 0), (x, self.height)], fill=(60, 60, 70), width=2)
        for y in range(0, self.height, 100):
            draw.line([(0, y), (self.width, y)], fill=(60, 60, 70), width=2)

        # Coffins
        for i in range(3):
            cx = self.width // 4 + i * (self.width // 4)
            cy = self.height // 2
            draw.rectangle(
                [cx - 40, cy - 60, cx + 40, cy + 60],
                fill=(100, 80, 60),
                outline=(60, 50, 40)
            )

    def _draw_sea(self, draw: ImageDraw.ImageDraw):
        """Draw sea/water features"""
        # Waves
        for i in range(5):
            y = int(self.height * (0.2 + i * 0.15))
            for x in range(0, self.width, 80):
                draw.arc(
                    [(x, y - 20), (x + 80, y + 20)],
                    0, 180,
                    fill=(100, 150, 200),
                    width=2
                )
