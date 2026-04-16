#!/usr/bin/env python3
"""
Retro Terminal Display Components for Call of Cthulhu
Provides styled output using box-drawing characters and colors
"""

import os
import sys
from typing import List, Optional, Tuple
from .color_system import get_colors, orange, green, cyan, red, yellow, gray, white


class RetroDisplay:
    """Base class for retro-styled terminal output"""

    # Box-drawing characters
    BOX_CHARS = {
        "top_left": "╔",
        "top_right": "╗",
        "bottom_left": "╚",
        "bottom_right": "╝",
        "horizontal": "═",
        "vertical": "║",
        "divider": "─",
        "cross": "╬",
    }

    def __init__(self, width: int = 80):
        """
        Initialize display.

        Args:
            width: Terminal width (default 80 characters)
        """
        self.width = width
        self.colors = get_colors()

    def clear(self) -> None:
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def print_box(
        self,
        title: str,
        content: str,
        color: str = "cyan",
        width: Optional[int] = None
    ) -> None:
        """
        Print text in a colored box.

        Args:
            title: Box title
            content: Box content (can be multi-line)
            color: Color scheme (orange, green, cyan)
            width: Box width (uses self.width if None)
        """
        width = width or self.width
        lines = content.split('\n')

        # Top border
        border = self.BOX_CHARS["top_left"] + self.BOX_CHARS["horizontal"] * (width - 2) + self.BOX_CHARS["top_right"]
        print(self.colors.colorize(border, color))

        # Title (if provided)
        if title:
            title_text = f" {title} "
            padding = (width - 2 - len(title_text)) // 2
            title_line = (
                self.BOX_CHARS["vertical"] +
                " " * padding +
                title_text +
                " " * (width - 2 - padding - len(title_text)) +
                self.BOX_CHARS["vertical"]
            )
            print(self.colors.colorize(title_line, color, bold=True))

            # Divider after title
            divider = self.BOX_CHARS["vertical"] + self.BOX_CHARS["divider"] * (width - 2) + self.BOX_CHARS["vertical"]
            print(self.colors.colorize(divider, color))

        # Content lines
        for line in lines:
            # Pad line to width
            padded_line = line[:width-2].ljust(width - 2)
            box_line = self.BOX_CHARS["vertical"] + " " + padded_line + " " + self.BOX_CHARS["vertical"]
            print(self.colors.colorize(box_line, color))

        # Bottom border
        border = self.BOX_CHARS["bottom_left"] + self.BOX_CHARS["horizontal"] * (width - 2) + self.BOX_CHARS["bottom_right"]
        print(self.colors.colorize(border, color))
        print()

    def print_header(self, text: str, color: str = "orange", width: Optional[int] = None) -> None:
        """
        Print a styled header.

        Args:
            text: Header text
            color: Header color
            width: Header width
        """
        width = width or self.width
        # Centered header with decorative elements
        padding = (width - len(text) - 4) // 2
        header = (
            "─" * padding +
            " ▌ " +
            text +
            " ▐ " +
            "─" * (width - padding - len(text) - 6)
        )
        print(self.colors.colorize(header, color, bold=True))
        print()

    def print_divider(self, char: str = "─", color: str = "cyan") -> None:
        """
        Print a decorative divider line.

        Args:
            char: Character to use for divider
            color: Divider color
        """
        divider = char * self.width
        print(self.colors.colorize(divider, color))
        print()

    def print_stat_bar(
        self,
        label: str,
        current: int,
        maximum: int,
        width: int = 20,
        color: str = "green"
    ) -> str:
        """
        Create a visual progress/stat bar.

        Args:
            label: Stat label
            current: Current value
            maximum: Maximum value
            width: Bar width
            color: Bar color

        Returns:
            Formatted stat bar string
        """
        percentage = (current / maximum) * 100 if maximum > 0 else 0
        filled = int((current / maximum) * width) if maximum > 0 else 0

        # Choose color based on percentage
        if percentage <= 25:
            bar_color = "red"
        elif percentage <= 50:
            bar_color = "yellow"
        else:
            bar_color = color

        bar = "█" * filled + "░" * (width - filled)
        return f"{label}: [{self.colors.colorize(bar, bar_color)}] {current:3d}/{maximum:3d}"

    def print_centered(self, text: str, color: str = "white", bold: bool = False) -> None:
        """
        Print centered text.

        Args:
            text: Text to center
            color: Text color
            bold: Bold text
        """
        padding = (self.width - len(text)) // 2
        centered = " " * padding + text
        print(self.colors.colorize(centered, color, bold=bold))

    def print_columns(
        self,
        cols: List[str],
        color: str = "white",
        separator: str = "  •  "
    ) -> None:
        """
        Print multiple columns of text.

        Args:
            cols: List of column texts
            color: Text color
            separator: Separator between columns
        """
        combined = separator.join(cols)
        # Truncate if too long
        if len(combined) > self.width:
            combined = combined[:self.width-3] + "..."
        print(self.colors.colorize(combined, color))

    def print_item_list(
        self,
        items: List[Tuple[str, str]],
        color: str = "green"
    ) -> None:
        """
        Print a formatted item list.

        Args:
            items: List of (item_name, description) tuples
            color: List color
        """
        for item, desc in items:
            item_text = self.colors.colorize(f"▸ {item}", color, bold=True)
            print(f"{item_text} — {desc}")

    def print_stat_display(
        self,
        stats: dict,
        color: str = "cyan"
    ) -> None:
        """
        Print a game state stat display.

        Args:
            stats: Dictionary of stat_name -> (current, max) tuples
            color: Display color
        """
        for stat_name, (current, maximum) in stats.items():
            print(self.print_stat_bar(stat_name, current, maximum, color=color))


class GameStateDisplay(RetroDisplay):
    """Display game state with stats and location"""

    def render(self, engine: 'GenerativeGameEngine') -> None:
        """
        Render game state display.

        Args:
            engine: Game engine instance
        """
        inv = engine.state.investigator
        state = engine.state

        # Character info
        self.print_header(f"CHARACTER: {inv.name}", color="orange")

        # Stats line
        stats_line = f"HP: {inv.characteristics['HP']:3d}/{inv.characteristics.get('max_hp', inv.characteristics['HP']):3d}  •  " \
                     f"SAN: {inv.characteristics['SAN']:3d}/{inv.characteristics.get('max_san', 99):3d}  •  " \
                     f"Turn: {state.turn}"
        print(self.colors.colorize(stats_line, "green"))

        # Stat bars
        hp_max = inv.characteristics.get('max_hp', inv.characteristics['HP'])
        san_max = inv.characteristics.get('max_san', 99)
        print(self.print_stat_bar("HP", inv.characteristics['HP'], hp_max, color="red"))
        print(self.print_stat_bar("SAN", inv.characteristics['SAN'], san_max, color="yellow"))

        # Location and inventory preview
        location = state.location or "Unknown"
        inventory_count = len(inv.inventory)
        companions = len(engine.companion_manager.get_active_companions())

        self.print_divider()
        self.print_columns([
            f"📍 {location}",
            f"🎒 {inventory_count} items",
            f"👥 {companions} companions"
        ], color="cyan")
        self.print_divider()


class NarrativeDisplay(RetroDisplay):
    """Display narrative text with streaming support"""

    def render_narrative(self, text: str, speaker: str = "DM") -> None:
        """
        Render narrative text with speaker label.

        Args:
            text: Narrative text
            speaker: Who is speaking (DM, NPC, System)
        """
        self.print_header(f"{speaker}", color="cyan")

        # Wrap text if needed
        lines = self._wrap_text(text, self.width - 4)
        for line in lines:
            print(f"  {line}")
        print()

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """
        Wrap text to fit width.

        Args:
            text: Text to wrap
            width: Maximum width

        Returns:
            List of wrapped lines
        """
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

    def stream_narrative(
        self,
        on_chunk,
        text: str,
        speaker: str = "DM"
    ) -> None:
        """
        Display narrative with streaming support.

        Args:
            on_chunk: Callback for streaming chunks
            text: Narrative text
            speaker: Speaker label
        """
        self.print_header(f"{speaker}", color="cyan")
        print("  ", end="", flush=True)

        # Stream the text
        chars_on_line = 2
        for chunk in text:
            sys.stdout.write(chunk)
            sys.stdout.flush()
            chars_on_line += len(chunk)

            # Word wrap at terminal width
            if chars_on_line > self.width - 4:
                print("\n  ", end="", flush=True)
                chars_on_line = 2

        print()
        print()


class InventoryDisplay(RetroDisplay):
    """Display character inventory"""

    def render(self, items: List[dict]) -> None:
        """
        Render inventory display.

        Args:
            items: List of item dictionaries with 'name' and 'description'
        """
        self.print_header("INVENTORY", color="green")

        if not items:
            print(self.colors.colorize("  Empty", "gray"))
        else:
            for item in items:
                name = item.get('name', 'Unknown')
                desc = item.get('description', '')
                print(self.colors.colorize(f"  ▸ {name}", "green", bold=True))
                if desc:
                    print(f"    {gray(desc)}")
        print()


class DialogueDisplay(RetroDisplay):
    """Display NPC dialogue"""

    def render(
        self,
        npc_name: str,
        npc_role: str,
        dialogue: str,
        reputation: int = 0
    ) -> None:
        """
        Render NPC dialogue.

        Args:
            npc_name: NPC name
            npc_role: NPC occupation/role
            dialogue: Dialogue text
            reputation: Reputation level (-100 to +100)
        """
        # Reputation label
        if reputation > 50:
            rep_label = green("TRUSTED", bold=True)
        elif reputation > 0:
            rep_label = green("FRIENDLY", bold=True)
        elif reputation < -50:
            rep_label = red("HOSTILE", bold=True)
        else:
            rep_label = gray("NEUTRAL")

        title = f"{npc_name} ({npc_role}) [{rep_label}]"
        self.print_header(title, color="cyan")

        # Dialogue text
        lines = self._wrap_text(dialogue, self.width - 4)
        for line in lines:
            print(f"  {line}")
        print()


class EndingDisplay(RetroDisplay):
    """Display game ending"""

    def render(
        self,
        ending_type: str,
        narrative: str,
        stats: dict
    ) -> None:
        """
        Render game ending screen.

        Args:
            ending_type: Type of ending (triumph, madness, etc.)
            narrative: Ending narrative text
            stats: Final game statistics
        """
        self.clear()
        self.print_centered("◇ GAME OVER ◇", color="orange", bold=True)
        self.print_divider(color="orange")

        # Ending title
        self.print_centered(
            f"🔮 {ending_type.upper().replace('_', ' ')} 🔮",
            color="orange",
            bold=True
        )

        self.print_divider()

        # Narrative
        lines = self._wrap_text(narrative, self.width - 4)
        for line in lines:
            print(f"  {line}")

        self.print_divider()

        # Final statistics
        print(self.colors.colorize("FINAL STATISTICS:", "cyan", bold=True))
        for key, value in stats.items():
            print(f"  {key}: {value}")

        self.print_divider()
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


# Test function
if __name__ == "__main__":
    display = RetroDisplay()
    display.clear()

    # Test header
    display.print_header("GAME STATE", color="orange")

    # Test box
    display.print_box(
        "Test Box",
        "This is a test box\nWith multiple lines\nOf content",
        color="cyan"
    )

    # Test stat bar
    print(display.print_stat_bar("HP", 12, 14, color="red"))
    print(display.print_stat_bar("SAN", 75, 99, color="yellow"))

    # Test centered text
    display.print_centered("Centered Text Here", color="green", bold=True)

    # Test divider
    display.print_divider(color="cyan")

    print("✓ Display tests complete")
