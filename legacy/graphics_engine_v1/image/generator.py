#!/usr/bin/env python3
"""
Image Generator - Enhanced Procedural image generation using Perlin noise
Generates high-quality 640x480 retro pixel art images for Lovecraftian horror
"""

from PIL import Image, ImageDraw, ImageFilter
import random
import math
from .palette import get_palette, interpolate_color


class ProceduralImageGenerator:
    """Generate high-quality pixel art images using Perlin noise and procedural rules"""

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

        # Generate multi-layer terrain
        terrain = self._generate_terrain(seed)

        # Apply atmospheric effects based on location
        atmosphere = self._generate_atmosphere(location, seed)

        # Paint pixels with enhanced quality
        for y in range(self.height):
            for x in range(self.width):
                # Get base terrain value
                value = terrain[y][x]

                # Apply atmosphere effect
                atmos = atmosphere[y][x]
                value = value * (0.8 + atmos * 0.2)  # Blend with atmosphere

                # Map to color from palette
                color = interpolate_color(value, palette)

                # Apply enhanced dithering and texture
                color = self._apply_texture(color, x, y, value, seed)

                pixels[x, y] = color

        # Draw location-specific details on top
        self._draw_details(img, location, seed)

        # Apply atmospheric overlay (now returns modified image)
        img = self._apply_atmospheric_effects(img, location, seed)

        return img

    def _generate_terrain(self, seed: int) -> list:
        """
        Generate multi-octave Perlin-like noise terrain.
        Uses multiple scales for more interesting features.

        Args:
            seed: Random seed

        Returns:
            2D list of values from 0.0 to 1.0
        """
        try:
            from perlin_noise import PerlinNoise

            # Multiple octaves for layered complexity
            noise1 = PerlinNoise(octaves=6, seed=seed)
            noise2 = PerlinNoise(octaves=10, seed=seed + 1)
            noise3 = PerlinNoise(octaves=14, seed=seed + 2)

            terrain = []
            for y in range(self.height):
                row = []
                for x in range(self.width):
                    # Multi-scale sampling
                    nx = x / 150.0
                    ny = y / 150.0

                    # Layer 1: Large features
                    v1 = noise1([nx, ny]) * 0.5

                    # Layer 2: Medium features
                    v2 = noise2([nx * 1.5, ny * 1.5]) * 0.3

                    # Layer 3: Fine details
                    v3 = noise3([nx * 3, ny * 3]) * 0.2

                    value = v1 + v2 + v3

                    # Normalize to 0-1
                    value = (value + 1.5) / 3.0
                    value = max(0.0, min(1.0, value))

                    row.append(value)
                terrain.append(row)

            return terrain

        except ImportError:
            # Fallback: complex gradient
            return self._generate_advanced_gradient(seed)

    def _generate_atmosphere(self, location: str, seed: int) -> list:
        """
        Generate atmospheric effects (fog, haze, light).

        Args:
            location: Location name
            seed: Random seed

        Returns:
            2D list of atmospheric values
        """
        try:
            from perlin_noise import PerlinNoise
            noise = PerlinNoise(octaves=4, seed=seed + 100)

            atmosphere = []
            for y in range(self.height):
                row = []
                for x in range(self.width):
                    # Atmospheric haze
                    value = noise([x / 200.0, y / 200.0])

                    # Add distance fog (darker at edges)
                    distance = math.sqrt((x - self.width/2)**2 + (y - self.height/2)**2)
                    distance = distance / math.sqrt((self.width/2)**2 + (self.height/2)**2)
                    fog = 1.0 - (distance * 0.3)

                    value = value * fog
                    value = (value + 1.0) / 2.0
                    value = max(0.0, min(1.0, value))

                    row.append(value)
                atmosphere.append(row)

            return atmosphere

        except ImportError:
            # Simple gradient fallback
            return [[0.5 for _ in range(self.width)] for _ in range(self.height)]

    def _apply_texture(self, color: tuple, x: int, y: int, value: float, seed: int) -> tuple:
        """
        Apply texture and dithering to color.

        Args:
            color: Base RGB color
            x, y: Pixel coordinates
            value: Noise value at this position
            seed: Random seed

        Returns:
            Modified RGB color
        """
        r, g, b = color

        # Ordered dithering (Bayer pattern)
        bayer = [
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5]
        ]

        # Apply Bayer dithering
        bx = (x % 4)
        by = (y % 4)
        dither = (bayer[by][bx] - 8) * 2

        r = max(0, min(255, r + dither))
        g = max(0, min(255, g + dither))
        b = max(0, min(255, b + dither))

        # Add slight random noise variation (perlin-based)
        random.seed(seed + x * 1000 + y)
        if random.random() < 0.05:  # 5% random variation
            amount = random.randint(-10, 10)
            r = max(0, min(255, r + amount))
            g = max(0, min(255, g + amount))
            b = max(0, min(255, b + amount))

        return (r, g, b)

    def _generate_advanced_gradient(self, seed: int) -> list:
        """
        Generate advanced gradient terrain (fallback).

        Args:
            seed: Random seed

        Returns:
            2D list of values
        """
        random.seed(seed)
        terrain = [[0.0 for _ in range(self.width)] for _ in range(self.height)]

        # Multiple sine wave combinations for interesting patterns
        for y in range(self.height):
            for x in range(self.width):
                nx = x / 100.0
                ny = y / 100.0

                # Layered sine waves
                v1 = math.sin(nx * 0.5) * 0.3
                v2 = math.cos(ny * 0.7) * 0.3
                v3 = math.sin((nx + ny) * 1.5) * 0.2
                v4 = math.cos((nx - ny) * 2.0) * 0.2

                value = v1 + v2 + v3 + v4
                value = (value + 1.0) / 2.0
                terrain[y][x] = value

        return terrain

    def _draw_details(self, img: Image.Image, location: str, seed: int):
        """
        Draw location-specific detailed features.

        Args:
            img: PIL Image to draw on
            location: Location name
            seed: Random seed
        """
        random.seed(seed)
        draw = ImageDraw.ImageDraw(img)

        location_lower = location.lower()

        if "lighthouse" in location_lower:
            if "interior" in location_lower:
                self._draw_lighthouse_interior_details(draw, seed)
            else:
                self._draw_lighthouse_exterior_details(draw, seed)
        elif "forest" in location_lower:
            self._draw_forest_details(draw, seed)
        elif "crypt" in location_lower:
            self._draw_crypt_details(draw, seed)
        elif "sea" in location_lower or "beach" in location_lower:
            self._draw_sea_details(draw, seed)
        elif "cave" in location_lower:
            self._draw_cave_details(draw, seed)
        elif "village" in location_lower:
            self._draw_village_details(draw, seed)

    def _draw_lighthouse_exterior_details(self, draw: ImageDraw.ImageDraw, seed: int):
        """Draw enhanced lighthouse exterior with advanced lighting"""
        random.seed(seed)

        # Main tower - more detailed with enhanced shading
        tower_x = self.width // 2
        tower_y = self.height // 2
        tower_width = 90
        tower_height = 320

        # Tower base with sophisticated gradient effect
        for i in range(0, tower_width, 3):
            # Left side darker (shadow)
            left_shade = max(20, 120 - i * 3)
            right_shade = min(200, 80 + i * 2)
            shade_l = (left_shade, left_shade, left_shade)
            shade_r = (right_shade, right_shade, right_shade)

            # Draw gradient stripes
            draw.line(
                [(tower_x - tower_width//2 + i, tower_y - tower_height//2),
                 (tower_x - tower_width//2 + i, tower_y + tower_height//2)],
                fill=shade_l if i < tower_width//2 else shade_r,
                width=3
            )

        # Tower outline with enhanced depth
        draw.rectangle(
            [tower_x - tower_width//2, tower_y - tower_height//2,
             tower_x + tower_width//2, tower_y + tower_height//2],
            outline=(60, 60, 70),
            width=4
        )
        draw.rectangle(
            [tower_x - tower_width//2 + 2, tower_y - tower_height//2 + 2,
             tower_x + tower_width//2 - 2, tower_y + tower_height//2 - 2],
            outline=(100, 100, 110),
            width=1
        )

        # Windows/details on tower with light effect
        for window_y in range(tower_y - tower_height//2 + 40, tower_y, 60):
            # Left window (darker)
            draw.rectangle(
                [tower_x - 25, window_y, tower_x - 5, window_y + 20],
                fill=(20, 20, 30),
                outline=(40, 40, 50)
            )
            # Add light reflection
            draw.line([(tower_x - 22, window_y + 2), (tower_x - 8, window_y + 2)],
                     fill=(50, 50, 70), width=1)

            # Right window (lighter interior)
            draw.rectangle(
                [tower_x + 5, window_y, tower_x + 25, window_y + 20],
                fill=(40, 40, 60),
                outline=(60, 60, 70)
            )
            draw.line([(tower_x + 8, window_y + 2), (tower_x + 22, window_y + 2)],
                     fill=(80, 80, 100), width=1)

        # Light room - enhanced with glow
        light_y = tower_y - tower_height//2 - 40
        draw.ellipse(
            [tower_x - 60, light_y - 35,
             tower_x + 60, light_y + 35],
            fill=(130, 130, 140),
            outline=(80, 80, 90),
            width=2
        )
        # Inner light glow
        draw.ellipse(
            [tower_x - 50, light_y - 25,
             tower_x + 50, light_y + 25],
            fill=(180, 180, 190),
            outline=(150, 150, 160),
            width=1
        )

        # Beacon - with sophisticated glow and rays
        for i in range(40, 0, -3):
            glow_intensity = int(255 * (1.0 - (i / 40.0) ** 1.5))
            color_val = min(255, glow_intensity)
            orange_val = min(200, glow_intensity * 0.8)
            draw.ellipse(
                [tower_x - i, light_y - i//2, tower_x + i, light_y + i//2],
                outline=(color_val, orange_val, 20),
                width=1
            )

        # Light rays from beacon
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(angle)
            ray_len = 200
            end_x = tower_x + int(ray_len * math.cos(rad))
            end_y = light_y + int(ray_len * math.sin(rad))
            draw.line([(tower_x, light_y), (end_x, end_y)],
                     fill=(200, 180, 100, 80), width=1)

        # Door - with enhanced shadows and detail
        door_x1, door_y1 = tower_x - 25, tower_y + tower_height//2 - 60
        door_x2, door_y2 = tower_x + 25, tower_y + tower_height//2

        # Door shadow
        draw.rectangle([door_x1 - 3, door_y1, door_x2 + 3, door_y2 + 8],
                      fill=(20, 20, 20))

        draw.rectangle([door_x1, door_y1, door_x2, door_y2], fill=(80, 50, 25), outline=(40, 25, 10), width=3)
        # Door detail - panels
        draw.rectangle([door_x1 + 5, door_y1 + 5, door_x2 - 5, (door_y1 + door_y2) // 2 - 5],
                      outline=(50, 30, 15), width=1)
        draw.rectangle([door_x1 + 5, (door_y1 + door_y2) // 2 + 5, door_x2 - 5, door_y2 - 5],
                      outline=(50, 30, 15), width=1)
        # Door handle - brass with shine
        handle_x = door_x2 - 8
        handle_y = (door_y1 + door_y2) // 2
        draw.ellipse([handle_x - 5, handle_y - 5, handle_x + 5, handle_y + 5],
                    fill=(220, 200, 120))
        draw.ellipse([handle_x - 3, handle_y - 3, handle_x + 3, handle_y + 3],
                    fill=(240, 220, 140))

        # Cottage - more detailed with shadows
        cottage_x = tower_x - 180
        cottage_y = tower_y + 80
        cottage_w, cottage_h = 80, 50

        # Cottage shadow
        draw.rectangle(
            [cottage_x - cottage_w - 2, cottage_y - cottage_h,
             cottage_x + cottage_w + 2, cottage_y + cottage_h + 10],
            fill=(30, 30, 30))

        # Cottage walls
        draw.rectangle(
            [cottage_x - cottage_w, cottage_y - cottage_h,
             cottage_x + cottage_w, cottage_y + cottage_h],
            fill=(200, 160, 120),
            outline=(100, 75, 50),
            width=2
        )

        # Wall texture
        for tx in range(cottage_x - cottage_w + 5, cottage_x + cottage_w, 15):
            draw.line([(tx, cottage_y - cottage_h), (tx, cottage_y + cottage_h)],
                     fill=(160, 120, 80), width=1)

        # Cottage roof - triangular with shading
        draw.polygon(
            [(cottage_x - cottage_w - 10, cottage_y - cottage_h),
             (cottage_x + cottage_w + 10, cottage_y - cottage_h),
             (cottage_x, cottage_y - cottage_h - 70)],
            fill=(100, 65, 40),
            outline=(60, 40, 20)
        )
        # Roof highlight
        draw.polygon(
            [(cottage_x - cottage_w - 5, cottage_y - cottage_h + 2),
             (cottage_x, cottage_y - cottage_h - 65),
             (cottage_x + 30, cottage_y - cottage_h + 2)],
            fill=(130, 85, 55))

        # Cottage windows with light
        for wx in [cottage_x - 30, cottage_x + 30]:
            # Window shadow
            draw.rectangle([wx - 14, cottage_y - 12, wx + 14, cottage_y + 12],
                          fill=(10, 10, 15))
            # Window frame
            draw.rectangle([wx - 12, cottage_y - 10, wx + 12, cottage_y + 10],
                          fill=(30, 30, 45),
                          outline=(70, 60, 50))
            # Window light reflection
            draw.rectangle([wx - 8, cottage_y - 6, wx - 2, cottage_y - 2],
                          fill=(100, 100, 120))

        # Ground shadows with depth
        draw.line([(0, tower_y + tower_height//2 + 20), (self.width, tower_y + tower_height//2 + 20)],
                  fill=(10, 10, 10), width=50)
        draw.line([(0, tower_y + tower_height//2 + 25), (self.width, tower_y + tower_height//2 + 25)],
                  fill=(40, 40, 40), width=20)

    def _draw_lighthouse_interior_details(self, draw: ImageDraw.ImageDraw, seed: int):
        """Draw enhanced lighthouse interior with sophisticated lighting"""
        random.seed(seed)

        center_x = self.width // 2
        center_y = self.height // 2

        # Wall segments with depth and shadow
        for wall_x in range(0, self.width, 120):
            # Dark primary line
            draw.rectangle([wall_x, 0, wall_x + 3, self.height], fill=(30, 30, 40), width=0)
            # Light edge (highlight)
            draw.rectangle([wall_x + 3, 0, wall_x + 5, self.height], fill=(80, 80, 100), width=0)
            # Texture
            for ty in range(0, self.height, 30):
                draw.line([(wall_x + 1, ty), (wall_x + 4, ty + 15)], fill=(50, 50, 60), width=1)

        for wall_y in range(0, self.height, 100):
            # Dark primary line
            draw.rectangle([0, wall_y, self.width, wall_y + 3], fill=(30, 30, 40), width=0)
            # Light edge
            draw.rectangle([0, wall_y + 3, self.width, wall_y + 5], fill=(80, 80, 100), width=0)

        # Spiral staircase - more sophisticated
        for i in range(25):
            angle = (i / 25.0) * 6.28
            x = center_x + int(110 * math.cos(angle))
            y = center_y + int(85 * math.sin(angle))
            radius = 35 - i

            if radius > 2:
                # Shadow side
                draw.ellipse(
                    [x - radius - 1, y - radius - 1, x + radius + 1, y + radius + 1],
                    outline=(60, 60, 70),
                    width=1
                )
                # Main stair
                draw.ellipse(
                    [x - radius, y - radius, x + radius, y + radius],
                    outline=(110, 90, 70),
                    width=2
                )
                # Light reflection on stairs
                if i % 3 == 0:
                    draw.ellipse(
                        [x - radius + 3, y - radius + 1, x + radius - 3, y - radius + 6],
                        outline=(150, 130, 100),
                        width=1
                    )

        # Torches/light sources with advanced glow
        torch_positions = [(100, 100), (self.width - 100, 100),
                          (100, self.height - 100), (self.width - 100, self.height - 100)]

        for tx, ty in torch_positions:
            # Torch glow rings
            for glow_r in range(80, 0, -10):
                glow_val = int(255 * (1.0 - (glow_r / 80.0) ** 1.2))
                draw.ellipse([tx - glow_r, ty - glow_r, tx + glow_r, ty + glow_r],
                           outline=(glow_val, int(glow_val * 0.6), 0),
                           width=1)

            # Torch flame - bright center
            draw.ellipse([tx - 20, ty - 30, tx + 20, ty + 20],
                       fill=(250, 180, 50), outline=(200, 130, 0), width=2)
            # Flame center
            draw.ellipse([tx - 10, ty - 15, tx + 10, ty + 5],
                       fill=(255, 200, 80), outline=(220, 160, 40), width=1)

            # Light rays from torches
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                ray_len = 120
                end_x = tx + int(ray_len * math.cos(rad))
                end_y = ty + int(ray_len * math.sin(rad))
                draw.line([(tx, ty), (end_x, end_y)],
                         fill=(200, 150, 50), width=1)

        # Ancient symbols on walls
        for sym_x in range(150, self.width, 200):
            for sym_y in range(150, self.height, 150):
                # Draw mystical symbols
                s = 20
                draw.polygon([(sym_x, sym_y - s), (sym_x + s, sym_y),
                             (sym_x, sym_y + s), (sym_x - s, sym_y)],
                            outline=(100, 80, 60), width=1)
                draw.ellipse([sym_x - s//2, sym_y - s//2,
                             sym_x + s//2, sym_y + s//2],
                            outline=(120, 100, 80), width=1)

    def _draw_forest_details(self, draw: ImageDraw.ImageDraw, seed: int):
        """Draw enhanced forest with depth and shadows"""
        random.seed(seed)

        # Forest floor texture
        for fy in range(self.height - 100, self.height, 5):
            shade_val = int(40 + (fy - (self.height - 100)) * 0.5)
            draw.line([(0, fy), (self.width, fy)],
                     fill=(shade_val // 3, shade_val // 2, shade_val // 4), width=1)

        for _ in range(30):  # More trees with better distribution
            x = random.randint(30, self.width - 30)
            y = random.randint(40, self.height - 180)
            depth = (y - 40) / (self.height - 180)  # 0 = far, 1 = near

            # Tree trunk with rich color variation and shadows
            trunk_dark = (random.randint(30, 60), random.randint(20, 40), random.randint(5, 15))
            trunk_light = (random.randint(70, 110), random.randint(50, 80), random.randint(20, 40))

            trunk_height = int(80 + depth * 80)
            trunk_width = int(8 + depth * 16)

            # Trunk shadow
            draw.rectangle(
                [x - trunk_width - 2, y, x + trunk_width + 2, y + trunk_height + 5],
                fill=(20, 15, 10)
            )

            # Left side (shadow)
            draw.rectangle(
                [x - trunk_width, y, x, y + trunk_height],
                fill=trunk_dark,
                outline=(20, 15, 10)
            )

            # Right side (light)
            draw.rectangle(
                [x, y, x + trunk_width, y + trunk_height],
                fill=trunk_light,
                outline=(40, 25, 10)
            )

            # Bark texture
            for bark_y in range(y, y + trunk_height, 15):
                draw.line([(x - trunk_width + 2, bark_y),
                          (x - trunk_width + 6, bark_y + 3)],
                         fill=(trunk_dark[0] - 10, trunk_dark[1] - 8, trunk_dark[2] - 5), width=1)

            # Tree foliage - multiple sophisticated layers
            base_size = int(60 + depth * 50)

            for layer in range(3):
                size = base_size - layer * (base_size // 3)
                y_offset = layer * int(25 + depth * 15)

                # Dark side (back)
                dark_foliage = (random.randint(10, 35), random.randint(70, 110), random.randint(10, 35))
                # Light side (front)
                light_foliage = (random.randint(30, 70), random.randint(130, 180), random.randint(30, 70))

                # Foliage shadow
                draw.polygon(
                    [(x - size - 3, y - y_offset), (x + size + 3, y - y_offset),
                     (x, y - (150 + y_offset) - 3)],
                    fill=(20, 30, 15)
                )

                # Dark foliage (back)
                draw.polygon(
                    [(x - size, y - y_offset), (x, y - y_offset),
                     (x - size // 2, y - (150 + y_offset))],
                    fill=dark_foliage,
                    outline=(10, 40, 10)
                )

                # Light foliage (front)
                draw.polygon(
                    [(x, y - y_offset), (x + size, y - y_offset),
                     (x + size // 2, y - (150 + y_offset))],
                    fill=light_foliage,
                    outline=(15, 60, 15)
                )

                # Foliage highlights
                if layer == 0:
                    highlight_size = size // 3
                    draw.polygon(
                        [(x - highlight_size, y - y_offset - 10),
                         (x + highlight_size, y - y_offset - 10),
                         (x, y - (120 + y_offset))],
                        fill=(100, 160, 100)
                    )

    def _draw_crypt_details(self, draw: ImageDraw.ImageDraw, seed: int):
        """Draw enhanced crypt with stone texture and shadows"""
        random.seed(seed)

        # Stone grid with sophisticated depth and texture
        for x in range(0, self.width, 80):
            # Primary grout line (dark shadow)
            draw.line([(x, 0), (x, self.height)], fill=(25, 25, 35), width=4)
            # Grout highlight (light edge)
            draw.line([(x + 2, 0), (x + 2, self.height)], fill=(90, 90, 110), width=2)

        for y in range(0, self.height, 80):
            # Primary grout line
            draw.line([(0, y), (self.width, y)], fill=(25, 25, 35), width=4)
            # Grout highlight
            draw.line([(0, y + 2), (self.width, y + 2)], fill=(90, 90, 110), width=2)

        # Stone surface texture
        for sx in range(0, self.width, 40):
            for sy in range(0, self.height, 40):
                stone_shade = random.randint(60, 90)
                draw.rectangle([sx, sy, sx + 35, sy + 35],
                             fill=(stone_shade, stone_shade, stone_shade + 5))

                # Stone cracks
                if random.random() > 0.7:
                    crack_x = sx + random.randint(5, 30)
                    crack_y = sy + random.randint(5, 30)
                    draw.line([(crack_x, crack_y), (crack_x + random.randint(5, 15), crack_y + random.randint(5, 15))],
                             fill=(30, 30, 35), width=1)

        # Coffins with enhanced detail and shadows
        coffin_configs = [
            (self.width // 5, self.height // 2 - 30),
            (self.width * 2 // 5, self.height // 2 + 20),
            (self.width * 3 // 5, self.height // 2 - 25),
            (self.width * 4 // 5, self.height // 2 + 15),
        ]

        for cx, cy in coffin_configs:
            # Coffin shadow
            draw.rectangle(
                [cx - 52, cy - 72, cx + 52, cy + 72],
                fill=(20, 20, 25))

            # Coffin wood color variations
            wood_dark = (random.randint(70, 90), random.randint(50, 65), random.randint(30, 45))
            wood_light = (random.randint(100, 120), random.randint(75, 95), random.randint(45, 65))

            # Left side (shadow)
            draw.rectangle(
                [cx - 50, cy - 70, cx - 5, cy + 70],
                fill=wood_dark,
                outline=(35, 25, 15),
                width=2
            )

            # Right side (light)
            draw.rectangle(
                [cx - 5, cy - 70, cx + 50, cy + 70],
                fill=wood_light,
                outline=(50, 35, 20),
                width=2
            )

            # Coffin lid detail - ornate cross
            cross_top = cy - 40
            cross_size = 12
            draw.line([(cx - cross_size, cross_top), (cx + cross_size, cross_top)],
                     fill=(150, 120, 80), width=2)
            draw.line([(cx, cross_top - cross_size), (cx, cross_top + cross_size)],
                     fill=(150, 120, 80), width=2)

            # Coffin nameplate area
            draw.rectangle([cx - 35, cy + 30, cx + 35, cy + 55],
                         fill=(50, 40, 25),
                         outline=(70, 55, 35), width=1)

            # Interior detail - skeletal hint
            draw.polygon([(cx - 30, cy - 50), (cx + 30, cy - 50),
                         (cx + 20, cy + 50), (cx - 20, cy + 50)],
                        outline=(40, 30, 20), width=1)

            # Coffin bands
            for band_y in [cy - 30, cy + 10]:
                draw.rectangle([cx - 48, band_y - 2, cx + 48, band_y + 2],
                             fill=(120, 100, 70),
                             outline=(80, 60, 40), width=1)

    def _draw_sea_details(self, draw: ImageDraw.ImageDraw, seed: int):
        """Draw enhanced sea with sophisticated water effects"""
        random.seed(seed)

        # Depth-based water coloring - from deep blue to lighter
        for depth_layer in range(8):
            y_start = int(self.height * (0.1 + depth_layer * 0.1))
            y_end = int(self.height * (0.2 + depth_layer * 0.1))

            # Color gradient based on depth
            depth_ratio = depth_layer / 8.0
            water_dark = int(20 + depth_ratio * 40)
            water_blue = int(80 + depth_ratio * 80)
            water_light = int(150 + depth_ratio * 100)

            for y in range(y_start, min(y_end + 1, self.height)):
                for x in range(0, self.width, 3):  # Sample every 3 pixels for performance
                    # Add subtle variation
                    var = (x + y + seed) % 10
                    shade = water_dark + (var % 3) * 5
                    draw.line([(x, y), (x + 3, y)], fill=(shade, water_blue + var % 5, water_light + var % 3), width=1)

        # Wave patterns with enhanced perspective and detail
        for wave_layer in range(10):
            y = int(self.height * (0.1 + wave_layer * 0.08))
            wave_height = max(3, int(25 - wave_layer * 2.5))
            wave_amplitude = max(2, int(60 - wave_layer * 6))

            for x in range(0, self.width + 100, 80):
                x_offset = int(wave_amplitude * math.sin((x / 100.0) + (wave_layer * 0.5)))

                # Wave crest - foam and light
                crest_y = y - wave_height
                draw.polygon(
                    [(x + x_offset - 40, y),
                     (x + x_offset, crest_y),
                     (x + x_offset + 40, y)],
                    fill=(int(100 + wave_layer * 8), int(140 + wave_layer * 6), int(180 + wave_layer * 4))
                )

                # Foam (white) on crest
                if wave_layer < 6:
                    draw.polygon(
                        [(x + x_offset - 15, crest_y + 1),
                         (x + x_offset + 15, crest_y + 1),
                         (x + x_offset, crest_y - 3)],
                        fill=(200 + wave_layer * 5, 220 + wave_layer * 3, 240)
                    )

                # Wave shadow (darker trough)
                if wave_layer > 0:
                    draw.polygon(
                        [(x + x_offset - 35, y + 5),
                         (x + x_offset - 15, y + wave_height + 2),
                         (x + x_offset + 15, y + wave_height + 2),
                         (x + x_offset + 35, y + 5)],
                        fill=(int(50 + wave_layer * 4), int(90 + wave_layer * 5), int(130 + wave_layer * 6))
                    )

        # Distant horizon with gradient effect
        horizon_y = int(self.height * 0.15)
        for hy in range(max(0, horizon_y - 10), horizon_y + 10):
            ratio = (horizon_y - hy) / 20.0
            sky_val = int(100 + ratio * 100)
            water_val = int(140 + ratio * 60)
            for hx in range(0, self.width):
                blend = (hx + hy + seed) % 7
                color = (sky_val + blend % 3, water_val - blend % 2, sky_val + blend % 2)
                draw.point((hx, hy), fill=color)

    def _draw_cave_details(self, draw: ImageDraw.ImageDraw, seed: int):
        """Draw enhanced cave with sophisticated formations"""
        random.seed(seed)

        # Cave background with depth gradient
        for y in range(self.height):
            depth_ratio = y / self.height
            shadow_val = int(30 + depth_ratio * 40)
            for x in range(self.width):
                variation = (x + y + seed) % 5
                draw.point((x, y), fill=(shadow_val + variation - 2,
                                       shadow_val + variation - 3,
                                       shadow_val + variation - 1))

        # Stalactites (hanging from ceiling) with enhanced detail
        for _ in range(18):
            x = random.randint(30, self.width - 30)
            y_top = random.randint(15, int(self.height * 0.35))
            height = random.randint(50, 150)
            width = random.randint(10, 25)

            # Stalactite shadow
            draw.polygon(
                [(x - width - 2, y_top), (x + width + 2, y_top), (x + 1, y_top + height + 2)],
                fill=(25, 25, 30)
            )

            # Main stalactite with gradient
            for layer_h in range(0, height, 10):
                layer_ratio = layer_h / height
                stone_val = int(70 + layer_ratio * 30)
                layer_width = int(width * (1.0 - layer_ratio * 0.3))
                draw.polygon(
                    [(x - layer_width, y_top + layer_h),
                     (x + layer_width, y_top + layer_h),
                     (x, y_top + min(layer_h + 10, height))],
                    fill=(stone_val, stone_val - 5, stone_val - 10),
                    outline=(50, 45, 40)
                )

            # Mineral deposits on stalactite
            for mineral_y in range(y_top + 20, y_top + height, 30):
                draw.ellipse([x - 3, mineral_y, x + 3, mineral_y + 8],
                           fill=(150, 130, 100),
                           outline=(100, 80, 60))

        # Stalagmites (rising from floor) with enhanced detail
        for _ in range(12):
            x = random.randint(30, self.width - 30)
            y_bottom = self.height - random.randint(20, 80)
            height = random.randint(40, 100)
            width = random.randint(12, 28)

            # Stalagmite shadow
            draw.polygon(
                [(x - width - 2, y_bottom), (x + width + 2, y_bottom),
                 (x + 1, y_bottom - height - 2)],
                fill=(15, 15, 20)
            )

            # Main stalagmite with gradient
            for layer_h in range(0, height, 10):
                layer_ratio = layer_h / height
                stone_val = int(60 + layer_ratio * 40)
                layer_width = int(width * (1.0 - layer_ratio * 0.5))
                draw.polygon(
                    [(x - layer_width, y_bottom - layer_h),
                     (x + layer_width, y_bottom - layer_h),
                     (x, y_bottom - min(layer_h + 10, height))],
                    fill=(stone_val, stone_val - 5, stone_val - 15),
                    outline=(70, 60, 50)
                )

        # Underground water/pool reflections
        pool_y = int(self.height * 0.75)
        for pool_x in range(0, self.width, 150):
            pool_w = random.randint(80, 120)
            # Water surface with reflection effect
            for wy in range(pool_y, pool_y + 40):
                water_shade = int(50 + (wy - pool_y) * 1.5)
                draw.line([(pool_x, wy), (pool_x + pool_w, wy)],
                         fill=(water_shade // 2, water_shade - 10, water_shade), width=1)

            # Ripples
            for ripple_i in range(5):
                ripple_w = 10 + ripple_i * 5
                draw.ellipse([pool_x + pool_w // 2 - ripple_w,
                             pool_y - ripple_w,
                             pool_x + pool_w // 2 + ripple_w,
                             pool_y + ripple_w],
                           outline=(100, 120, 140, 40), width=1)

    def _draw_village_details(self, draw: ImageDraw.ImageDraw, seed: int):
        """Draw enhanced village with sophisticated architecture"""
        random.seed(seed)

        # Ground texture
        ground_y = int(self.height * 0.6)
        for gy in range(ground_y, self.height):
            shade = int(60 + (gy - ground_y) * 0.3)
            for gx in range(0, self.width):
                variation = (gx + gy + seed) % 8
                draw.point((gx, gy), fill=(shade + variation // 2,
                                          shade - variation // 3,
                                          shade - variation // 4))

        # Buildings with enhanced architectural details
        building_positions = [
            (self.width // 12, int(self.height * 0.5)),
            (self.width * 3 // 12, int(self.height * 0.45)),
            (self.width * 5 // 12, int(self.height * 0.55)),
            (self.width * 7 // 12, int(self.height * 0.48)),
            (self.width * 9 // 12, int(self.height * 0.52)),
            (self.width * 11 // 12, int(self.height * 0.49)),
        ]

        for bx, by in building_positions:
            bw = int(self.width * 0.13)
            bh = random.randint(90, 140)

            # Building shadow
            draw.rectangle(
                [bx - 2, by - 2, bx + bw + 4, by + bh + 6],
                fill=(30, 30, 35)
            )

            # Left wall (shadow)
            draw.rectangle(
                [bx, by, bx + bw // 2, by + bh],
                fill=(100, 80, 60),
                outline=(50, 40, 30),
                width=2
            )

            # Right wall (light)
            draw.rectangle(
                [bx + bw // 2, by, bx + bw, by + bh],
                fill=(150, 120, 90),
                outline=(70, 55, 40),
                width=2
            )

            # Brick/stone pattern (optimized - fewer bricks)
            for brick_row in range(by, by + bh, 20):
                for brick_col in range(bx, bx + bw, 25):
                    draw.rectangle([brick_col, brick_row, brick_col + 20, brick_row + 16],
                                 outline=(100, 80, 60), width=1)

            # Windows with lighting
            window_spacing = int(bw // 3)
            for wy in range(by + 20, by + bh - 20, 30):
                for window_x_offset in [window_spacing // 2, window_spacing + window_spacing // 2]:
                    wx = bx + window_x_offset
                    ww, wh = 16, 16

                    # Window glass shine
                    draw.rectangle([wx - ww // 2, wy - wh // 2,
                                   wx + ww // 2, wy + wh // 2],
                                 fill=(20, 20, 35),
                                 outline=(50, 45, 40), width=1)

                    # Light glow (some windows have light)
                    if random.random() > 0.4:
                        draw.rectangle([wx - ww // 2 + 2, wy - wh // 2 + 2,
                                       wx + ww // 2 - 2, wy + wh // 2 - 2],
                                     fill=(180, 160, 120))
                        # Window panes
                        draw.line([(wx - ww // 2, wy), (wx + ww // 2, wy)],
                                 fill=(100, 90, 70), width=1)
                        draw.line([(wx, wy - wh // 2), (wx, wy + wh // 2)],
                                 fill=(100, 90, 70), width=1)

            # Roof - triangular with shading
            roof_peak_y = by - int(bh * 0.3)
            roof_left = [bx - 5, by]
            roof_right = [bx + bw + 5, by]
            roof_peak = [bx + bw // 2, roof_peak_y]

            # Roof shadow
            draw.polygon([roof_left, roof_right, [roof_peak[0] + 1, roof_peak[1] + 1]],
                        fill=(50, 40, 30))

            # Roof left side (dark)
            draw.polygon([roof_left, roof_peak, [roof_left[0], roof_left[1] - 2]],
                        fill=(80, 60, 40),
                        outline=(50, 35, 20), width=1)

            # Roof right side (light)
            draw.polygon([roof_peak, roof_right, [roof_right[0], roof_right[1] - 2]],
                        fill=(110, 85, 60),
                        outline=(60, 45, 25), width=1)

            # Roof tiles pattern
            for tile_y in range(by - int(bh * 0.25), by, 8):
                for tile_x in range(bx, bx + bw, 12):
                    draw.ellipse([tile_x, tile_y, tile_x + 8, tile_y + 8],
                               outline=(70, 55, 40), width=1)

            # Door
            door_y = by + bh - 35
            door_w = int(bw * 0.25)
            draw.rectangle([bx + bw // 2 - door_w // 2, door_y,
                           bx + bw // 2 + door_w // 2, by + bh],
                         fill=(60, 40, 20),
                         outline=(35, 20, 10), width=2)

            # Door detail - frame
            draw.rectangle([bx + bw // 2 - door_w // 2 + 2, door_y + 2,
                           bx + bw // 2 + door_w // 2 - 2, by + bh - 2],
                         outline=(40, 25, 12), width=1)

    def _apply_watercolor_effect(self, img: Image.Image, seed: int) -> Image.Image:
        """
        Apply watercolor/artistic effect to make images look painted.

        Args:
            img: PIL Image
            seed: Random seed

        Returns:
            Watercolored image
        """
        random.seed(seed)

        # 1. Apply soft blur for watercolor effect
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

        # 2. Add watercolor wash effect (semi-transparent color splotches)
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.ImageDraw(overlay)

        # Create random watercolor washes
        for _ in range(15):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(40, 150)

            # Earth tone watercolor (browns, ochres, siennas)
            color_choices = [
                (160, 120, 80, 20),   # Brown
                (180, 140, 100, 15),  # Ochre
                (140, 100, 60, 20),   # Dark earth
                (200, 160, 120, 10),  # Light ochre
                (120, 90, 60, 18),    # Dark brown
            ]
            color = random.choice(color_choices)

            # Draw irregular watercolor spots
            for offset in range(0, size, 5):
                r = size - offset
                if r > 0:
                    alpha = max(0, color[3] - int(offset / size * color[3]))
                    overlay_draw.ellipse(
                        [x - r, y - r, x + r, y + r],
                        fill=(*color[:3], alpha)
                    )

        # Blend overlay with image
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')

        return img

    def _apply_atmospheric_effects(self, img: Image.Image, location: str, seed: int):
        """
        Apply atmospheric effects efficiently (watercolor + vignette).

        Args:
            img: PIL Image
            location: Location name
            seed: Random seed
        """
        # Apply watercolor effect first
        img = self._apply_watercolor_effect(img, seed)

        # Simple vignette overlay using PIL ImageDraw
        draw = ImageDraw.ImageDraw(img)

        # Vignette effect - darkened edges
        vignette_color = (0, 0, 0)
        for i in range(40):
            # Concentric rectangles getting darker toward edges
            alpha = int((i / 40) * 80)
            rect_size = int((40 - i) * (min(self.width, self.height) / 80))
            color_val = max(0, 20 - int(alpha * 0.3))

            x1 = (self.width // 2) - rect_size
            y1 = (self.height // 2) - int(rect_size * 0.75)
            x2 = (self.width // 2) + rect_size
            y2 = (self.height // 2) + int(rect_size * 0.75)

            if i % 4 == 0:  # Draw every 4th for performance
                draw.rectangle([x1, y1, x2, y2], outline=(color_val, color_val, color_val), width=1)

        return img
