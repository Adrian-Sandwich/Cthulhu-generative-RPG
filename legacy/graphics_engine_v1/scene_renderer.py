"""Render ASCII art scenes for game display"""
from pathlib import Path
from graphics_engine.ascii_converter import get_sample_ascii, list_samples
from ui.color_system import COLORS

SAMPLES_DIR = Path(__file__).parent / "data" / "art_samples"

# Map game locations to sample indices
LOCATION_SCENES = {
    "lighthouse_exterior": 0,
    "lighthouse_interior": 1,
    "forest": 5,
    "beach": 10,
    "village": 15,
    "crypt": 20,
    "sea": 25,
    "cave": 30,
}

class AsciiSceneRenderer:
    """Render ASCII art scenes from samples"""

    def __init__(self, width=80):
        self.width = width
        self.samples = list_samples()
        self.scenes = {}
        self._preload_scenes()

    def _preload_scenes(self):
        """Preload ASCII art for all mapped locations"""
        for location, index in LOCATION_SCENES.items():
            if index < len(self.samples):
                ascii_art = get_sample_ascii(index, self.width)
                if ascii_art:
                    self.scenes[location] = ascii_art

    def render_scene(self, location, colorized=False):
        """Render a scene for a game location"""
        if location in self.scenes:
            scene = self.scenes[location]
        else:
            # Fallback to first available scene
            scene = get_sample_ascii(0, self.width) or "No scene available"

        if colorized:
            scene = self._colorize_scene(scene, location)

        return scene

    def _colorize_scene(self, scene_text, location):
        """Add color codes to ASCII art based on location theme"""
        color_map = {
            "lighthouse": COLORS["yellow"],
            "forest": COLORS["green"],
            "beach": COLORS["cyan"],
            "village": COLORS["white"],
            "crypt": COLORS["magenta"],
            "sea": COLORS["blue"],
            "cave": COLORS["black"],
        }

        for keyword, color in color_map.items():
            if keyword in location:
                # Wrap scene in color
                return f"{color}{scene_text}{COLORS['reset']}"

        return scene_text

    def display_scene(self, location, title=None):
        """Display a formatted scene with optional title"""
        scene = self.render_scene(location, colorized=True)

        output = []
        if title:
            output.append(f"\n{COLORS['bold']}═══ {title} ═══{COLORS['reset']}\n")

        output.append(scene)
        output.append("")

        return "\n".join(output)

    def get_random_scene(self):
        """Get a random scene"""
        import random
        if self.samples:
            return get_sample_ascii(random.randint(0, len(self.samples) - 1), self.width)
        return None

    def scene_for_action(self, location, action_type):
        """Get appropriate scene for an action in a location"""
        action_scenes = {
            "arrive": "exterior" if "exterior" in location else "interior",
            "explore": "detailed",
            "combat": "tense",
            "discovery": "dramatic",
        }

        base_index = LOCATION_SCENES.get(location, 0)
        action_offset = hash(action_type) % 5

        index = (base_index + action_offset) % len(self.samples)
        return get_sample_ascii(index, self.width)

if __name__ == "__main__":
    renderer = AsciiSceneRenderer(width=60)

    # Demo: show a few scenes
    for location in ["lighthouse_exterior", "forest", "cave"]:
        print(renderer.display_scene(location, f"Location: {location}"))
        print("\n" + "=" * 60 + "\n")
