#!/usr/bin/env python3
"""
History Viewer - Display complete game history
Shows all turns, discoveries, decisions made
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional
from ui.color_system import orange, green, cyan, red, yellow, gray
from ui.retro_display import RetroDisplay


class HistoryViewer(RetroDisplay):
    """Displays complete game history with filtering and search"""

    def __init__(self, width: int = 80):
        super().__init__(width=width)
        self.current_page = 0
        self.lines_per_page = 20

    def display_full_history(
        self,
        narrative_turns: List[str],
        investigator_name: str,
        location: str,
        turn: int,
        discoveries: List[str] = None,
        stats: Dict = None
    ) -> None:
        """
        Display complete game history with metadata.

        Args:
            narrative_turns: All narrative beats so far
            investigator_name: Player character name
            location: Current location
            turn: Current turn number
            discoveries: List of discoveries made
            stats: Character stats (HP, SAN, etc.)
        """
        self.clear()

        # Header with game info
        print(orange("═" * self.width, bold=True))
        print(orange(f"GAME HISTORY: {investigator_name}".center(self.width), bold=True))
        print(orange(f"Turn {turn} | Location: {location}".center(self.width)))
        print(orange("═" * self.width, bold=True))
        print()

        # Game state summary
        if stats:
            print(cyan("CURRENT STATE:", bold=True))
            for key, value in stats.items():
                if isinstance(value, tuple):
                    print(f"  {key}: {value[0]}/{value[1]}")
                else:
                    print(f"  {key}: {value}")
            print()

        # Discoveries section
        if discoveries:
            print(green("DISCOVERIES:", bold=True))
            for i, discovery in enumerate(discoveries, 1):
                print(f"  {i}. {discovery}")
            print()

        # Full narrative history
        print(cyan("COMPLETE NARRATIVE:", bold=True))
        print(gray("─" * self.width))
        print()

        for i, turn_text in enumerate(narrative_turns, 1):
            # Color code based on speaker
            if turn_text.startswith("Player:"):
                colored_line = yellow(f"[Turn {i}] ") + green(turn_text.replace("Player: ", ""), bold=True)
            elif turn_text.startswith("DM:"):
                colored_line = yellow(f"[Turn {i}] ") + cyan(turn_text.replace("DM: ", ""))
            else:
                colored_line = yellow(f"[Turn {i}] ") + turn_text

            # Wrap text if needed
            lines = self._wrap_text(colored_line, self.width - 4)
            for line in lines:
                print(f"  {line}")
            print()

        print(gray("─" * self.width))
        print()

    def display_summary(
        self,
        investigator_name: str,
        occupation: str,
        turns_played: int,
        hp: int,
        max_hp: int,
        sanity: int,
        max_sanity: int,
        location: str,
        discoveries: List[str],
        inventory: List[str],
        companions: int,
        status: str = "In Progress"
    ) -> None:
        """
        Display game summary at a glance.

        Args:
            investigator_name: Character name
            occupation: Character occupation
            turns_played: Number of turns
            hp: Current HP
            max_hp: Max HP
            sanity: Current sanity
            max_sanity: Max sanity
            location: Current location
            discoveries: Discoveries made
            inventory: Items held
            companions: Number of companions
            status: Game status
        """
        self.clear()

        # Title
        print(orange("╔" + "═" * (self.width - 2) + "╗", bold=True))
        print(orange(f"║ GAME SUMMARY - {investigator_name}".ljust(self.width - 1) + "║", bold=True))
        print(orange("╚" + "═" * (self.width - 2) + "╝", bold=True))
        print()

        # Character info
        print(cyan("CHARACTER:", bold=True))
        print(f"  Name: {green(investigator_name, bold=True)}")
        print(f"  Occupation: {occupation}")
        print()

        # Stats
        print(cyan("VITALS:", bold=True))
        hp_bar = self.print_stat_bar("HP", hp, max_hp, width=25, color="red")
        san_bar = self.print_stat_bar("SAN", sanity, max_sanity, width=25, color="yellow")
        print(f"  {hp_bar}")
        print(f"  {san_bar}")
        print()

        # Progress
        print(cyan("PROGRESS:", bold=True))
        print(f"  Turns Played: {orange(str(turns_played), bold=True)}")
        print(f"  Current Location: {green(location, bold=True)}")
        print(f"  Game Status: {yellow(status, bold=True)}")
        print()

        # Discoveries
        print(cyan("DISCOVERIES:", bold=True))
        if discoveries:
            for i, disc in enumerate(discoveries, 1):
                # Truncate if too long
                if len(disc) > 70:
                    disc = disc[:67] + "..."
                print(f"  {i}. {disc}")
        else:
            print("  (None yet)")
        print()

        # Inventory
        print(cyan("INVENTORY:", bold=True))
        if inventory:
            for item in inventory:
                print(f"  • {item}")
        else:
            print("  (Empty)")
        print()

        # Companions
        print(cyan("COMPANIONS:", bold=True))
        if companions > 0:
            print(f"  {green(f'{companions} alive', bold=True)}")
        else:
            print(f"  {red('None alive', bold=True)}")
        print()

    def display_turn_detail(self, turn_number: int, narrative_turns: List[str]) -> None:
        """
        Display detailed view of a specific turn.

        Args:
            turn_number: Turn to display (1-indexed)
            narrative_turns: All narrative turns
        """
        self.clear()

        if turn_number < 1 or turn_number > len(narrative_turns):
            print(red(f"Turn {turn_number} not found"))
            return

        turn_text = narrative_turns[turn_number - 1]

        # Header
        print(orange(f"═" * self.width, bold=True))
        print(orange(f"TURN {turn_number} DETAIL".center(self.width), bold=True))
        print(orange(f"═" * self.width, bold=True))
        print()

        # Parse turn type
        if turn_text.startswith("Player:"):
            print(yellow("PLAYER ACTION:", bold=True))
            action = turn_text.replace("Player: ", "")
            lines = self._wrap_text(action, self.width - 4)
            for line in lines:
                print(f"  {line}")
        elif turn_text.startswith("DM:"):
            print(cyan("KEEPER NARRATION:", bold=True))
            narration = turn_text.replace("DM: ", "")
            lines = self._wrap_text(narration, self.width - 4)
            for line in lines:
                print(f"  {line}")
        else:
            print(turn_text)

        print()

    def display_timeline(self, narrative_turns: List[str], max_lines: int = 30) -> None:
        """
        Display a compact timeline of all turns.

        Args:
            narrative_turns: All narrative turns
            max_lines: Max lines to show
        """
        self.clear()

        print(orange("═" * self.width, bold=True))
        print(orange("GAME TIMELINE".center(self.width), bold=True))
        print(orange("═" * self.width, bold=True))
        print()

        # Show condensed timeline
        for i, turn in enumerate(narrative_turns, 1):
            if turn.startswith("Player:"):
                # Show player action in green
                action = turn.replace("Player: ", "")
                if len(action) > 60:
                    action = action[:57] + "..."
                print(f"  {yellow(f'[{i}]')} {green(action, bold=True)}")
            elif turn.startswith("DM:"):
                # Show DM response in cyan (abbreviated)
                response = turn.replace("DM: ", "")
                if len(response) > 60:
                    response = response[:57] + "..."
                print(f"      {cyan(response)}")

        print()

    def display_discoveries_log(self, discoveries: List[Dict]) -> None:
        """
        Display discoveries in organized log format.

        Args:
            discoveries: List of discovery dicts with turn, description, etc.
        """
        self.clear()

        print(orange("═" * self.width, bold=True))
        print(orange("DISCOVERIES LOG".center(self.width), bold=True))
        print(orange("═" * self.width, bold=True))
        print()

        if not discoveries:
            print(gray("No discoveries yet..."))
            print()
            return

        for i, disc in enumerate(discoveries, 1):
            turn = disc.get('turn', '?')
            location = disc.get('location', 'Unknown')
            description = disc.get('description', '')

            print(orange(f"DISCOVERY #{i}", bold=True))
            print(f"  Turn: {yellow(str(turn))}")
            print(f"  Location: {cyan(location)}")
            print(f"  Found: {green(description, bold=True)}")
            print()

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to fit width"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            if len(" ".join(current_line + [word])) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines
