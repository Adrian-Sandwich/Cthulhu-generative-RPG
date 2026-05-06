#!/usr/bin/env python3
"""
IMMERSIVE GAME ENGINE - Extends game_enhanced.py
Adds:
- ASCII art descriptions for atmosphere
- Object system (inventory, examine)
- Image support
- Rich environmental descriptions
"""

import json
from pathlib import Path
from .game_enhanced import EnhancedGameEngine
from .game_universal import Investigator


class ImmersiveGameEngine(EnhancedGameEngine):
    """Enhanced game with immersive features"""

    def __init__(self, entries_file):
        super().__init__(entries_file)
        self.entries_file = entries_file  # Store for immersive data loading
        self.objects = {}  # Global objects in entries
        self.inventory = []  # Player inventory
        self.atmosphere = {}  # Atmospheric descriptions per entry
        self.load_immersive_data()

    def load_immersive_data(self):
        """Load immersive data from companion JSON file"""
        # Look for entries_name.immersive.json
        immersive_file = Path(self.entries_file).stem + ".immersive.json"

        if Path(immersive_file).exists():
            with open(immersive_file, 'r') as f:
                data = json.load(f)
                self.objects = data.get('objects', {})
                self.atmosphere = data.get('atmosphere', {})
        else:
            # Create default
            self.generate_default_immersive()

    def generate_default_immersive(self):
        """Generate default immersive descriptions from entry metadata"""
        for num in range(1, self.base_engine.total_entries + 1):
            entry = self.base_engine.get_entry(num)
            if not entry:
                continue
            entry_type = entry.get('entry_type', 'adventure')

            # Generate atmosphere based on entry type
            if entry_type == 'horror':
                atmosphere = "The air is heavy with dread. Shadows seem deeper here."
            elif entry_type == 'combat':
                atmosphere = "Tension fills the space. Combat is imminent."
            elif entry_type == 'investigation':
                atmosphere = "Your senses are heightened. Details demand attention."
            elif entry_type == 'encounter':
                atmosphere = "You sense another presence nearby."
            else:
                atmosphere = "The atmosphere shifts around you."

            self.atmosphere[str(num)] = atmosphere

    def get_entry_display(self, entry_num):
        """Get full immersive display for entry"""
        entry = self.base_engine.get_entry(entry_num)
        if not entry:
            return None

        # Get atmospheric description
        atmosphere = self.atmosphere.get(str(entry_num), "The scene unfolds before you.")

        # Build display
        display = ""

        # Atmosphere first
        display += f"╔═══════════════════════════════════════════════════════════════════════════╗\n"
        display += f"║ {atmosphere:75} ║\n"
        display += f"╚═══════════════════════════════════════════════════════════════════════════╝\n\n"

        # Title if available
        if entry.get('metadata', {}).get('title'):
            title = entry['metadata']['title']
            display += f"█ {title}\n"
            display += f"{'─' * 80}\n\n"

        # Entry number and text
        text = entry.get('text', '')
        display += f"{text}\n"

        # Image reference if available
        if entry.get('metadata', {}).get('image'):
            image = entry['metadata']['image']
            display += f"\n[VISUAL: {image}]\n"

        # Metadata effects
        meta = entry.get('metadata', {})
        if meta.get('sanity_mod'):
            display += f"\n⚠️  Sanity loss: {meta['sanity_mod']}"
        if meta.get('hp_mod'):
            display += f"\n⚠️  Health loss: {meta['hp_mod']}"

        return display

    def display_entry_immersive(self, entry_num):
        """Display entry with full immersion"""
        display = self.get_entry_display(entry_num)
        if display:
            print(display)

    def examine_object(self, object_name):
        """Player examines an object in current location"""
        entry_num = self.game.current_entry

        if str(entry_num) in self.objects:
            entry_objects = self.objects[str(entry_num)]
            if object_name.lower() in entry_objects:
                return entry_objects[object_name.lower()]

        return None

    def get_inventory(self):
        """Get player inventory"""
        return self.inventory

    def add_to_inventory(self, item):
        """Add item to inventory"""
        if item not in self.inventory:
            self.inventory.append(item)
            return True
        return False

    def remove_from_inventory(self, item):
        """Remove item from inventory"""
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False

    def get_status_bar(self, inv_data):
        """Enhanced status bar with immersion"""
        inv = self.game.investigator
        chars = inv.characteristics

        # Sanity visualization
        san = chars['SAN']
        san_bar = "█" * int(san / 4) + "░" * (25 - int(san / 4))

        # Health visualization
        hp = chars['HP']
        hp_bar = "♥" * hp + "♡" * (15 - hp)

        status = f"{inv.name}\n"
        status += f"  HP: [{hp_bar}] {hp:2d}  │  SAN: [{san_bar}] {san:3d}  │  Luck: {chars['Luck']:2d}\n"

        # Inventory summary
        if self.inventory:
            status += f"  Items: {', '.join(self.inventory[:3])}"
            if len(self.inventory) > 3:
                status += f" +{len(self.inventory)-3}"

        return status


def create_immersive_game(entries_file, inv_data):
    """Factory function to create immersive game"""
    engine = ImmersiveGameEngine(entries_file)

    inv = Investigator(
        name=inv_data['name'],
        skills=inv_data['skills'],
        characteristics=inv_data['characteristics']
    )

    engine.create_game(inv, inv_data['starting_entry'])

    return engine
