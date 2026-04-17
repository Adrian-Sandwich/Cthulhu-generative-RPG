#!/usr/bin/env python3
"""
Color Palettes - Lovecraftian themes for retro pixel art
"""

# Color palettes for different locations/moods
PALETTES = {
    # Lighthouse exterior - misty, rocky, ominous
    "lighthouse_exterior": [
        (200, 180, 150),  # Sand/rock light
        (120, 100, 80),   # Rock dark
        (80, 100, 120),   # Ocean/sky
        (50, 50, 60),     # Deep water
        (30, 30, 40),     # Shadow
        (40, 40, 50),     # Very dark
    ],

    # Lighthouse interior - dark, ancient, eerie
    "lighthouse_interior": [
        (100, 100, 100),  # Stone light
        (60, 60, 70),     # Stone medium
        (40, 40, 50),     # Stone dark
        (20, 20, 30),     # Shadow
        (10, 10, 15),     # Deep shadow
        (80, 70, 60),     # Old metal
    ],

    # Forest/nature - twisted, unnatural
    "forest": [
        (34, 139, 34),    # Green
        (50, 100, 50),    # Dark green
        (139, 69, 19),    # Brown
        (25, 25, 25),     # Shadow
        (70, 50, 30),     # Trunk
        (100, 80, 60),    # Light earth
    ],

    # Crypt/underground - decaying, ancient
    "crypt": [
        (80, 80, 90),     # Stone light
        (50, 50, 60),     # Stone medium
        (30, 30, 40),     # Stone dark
        (15, 15, 20),     # Deep shadow
        (100, 90, 80),    # Bone/decay
        (60, 50, 40),     # Ancient wood
    ],

    # Cosmic/otherworldly - strange, alien
    "cosmic": [
        (100, 50, 150),   # Purple
        (150, 50, 100),   # Magenta
        (50, 50, 150),    # Deep blue
        (25, 25, 75),     # Very deep
        (200, 100, 200),  # Light purple
        (75, 25, 125),    # Dark purple
    ],

    # Sea/water - drowning, ancient depths
    "sea": [
        (50, 100, 150),   # Water light
        (30, 70, 120),    # Water medium
        (20, 50, 100),    # Water dark
        (10, 30, 70),     # Deep water
        (100, 150, 200),  # Foam
        (0, 20, 50),      # Abyss
    ],

    # Generic horror - dark, ominous
    "horror": [
        (80, 50, 60),     # Blood-dark
        (50, 30, 40),     # Shadow
        (100, 70, 80),    # Flesh
        (30, 20, 25),     # Deep shadow
        (120, 80, 90),    # Light flesh
        (40, 25, 30),     # Very dark
    ],
}

# Default palette (neutral)
DEFAULT_PALETTE = PALETTES["lighthouse_interior"]


def get_palette(location: str) -> list:
    """
    Get color palette for a location.

    Args:
        location: Location name (e.g., "lighthouse_exterior")

    Returns:
        List of RGB tuples
    """
    # Try exact match
    if location in PALETTES:
        return PALETTES[location]

    # Try to find closest match
    location_lower = location.lower()
    for key in PALETTES:
        if key.split("_")[0] in location_lower:
            return PALETTES[key]

    # Default
    return DEFAULT_PALETTE


def interpolate_color(value: float, palette: list) -> tuple:
    """
    Map value (0.0-1.0) to a color from palette.

    Args:
        value: Float between 0 and 1
        palette: List of RGB tuples

    Returns:
        RGB tuple
    """
    if not palette:
        return (128, 128, 128)

    # Clamp value
    value = max(0.0, min(1.0, value))

    # Map to palette index
    index = int(value * (len(palette) - 1))
    return palette[index]


# Additional color utilities
def darken(color: tuple, amount: float = 0.7) -> tuple:
    """Darken a color"""
    r, g, b = color
    return (int(r * amount), int(g * amount), int(b * amount))


def lighten(color: tuple, amount: float = 1.3) -> tuple:
    """Lighten a color"""
    r, g, b = color
    return (
        min(255, int(r * amount)),
        min(255, int(g * amount)),
        min(255, int(b * amount))
    )


def add_noise(color: tuple, noise_amount: int = 20) -> tuple:
    """Add slight random variation to color"""
    import random
    r, g, b = color
    r = max(0, min(255, r + random.randint(-noise_amount, noise_amount)))
    g = max(0, min(255, g + random.randint(-noise_amount, noise_amount)))
    b = max(0, min(255, b + random.randint(-noise_amount, noise_amount)))
    return (r, g, b)
