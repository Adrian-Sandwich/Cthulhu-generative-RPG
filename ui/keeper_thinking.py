#!/usr/bin/env python3
"""
Keeper Thinking - Animated loading state for Call of Cthulhu generative engine
Shows the DM (Keeper) contemplating the player's action with atmospheric visuals
"""

import time
import sys
from typing import Optional, Callable


class KeeperThinking:
    """Animated Keeper thinking state with progress bar"""

    # ASCII art frames for thinking animation (Lovecraftian theme)
    THINKING_FRAMES = [
        "The Keeper contemplates...",
        "The Keeper considers...",
        "The Keeper's mind writhes...",
        "The Keeper peers into darkness...",
        "The Keeper understands...",
    ]

    # Progress bar styles
    PROGRESS_BARS = {
        "standard": ("▮", "▯"),  # filled, empty
        "mystical": ("●", "○"),   # circle filled, empty
        "eldritch": ("▓", "░"),   # dark, light
        "cosmic": ("⬢", "⬡"),     # hexagon filled, empty
    }

    def __init__(self, style: str = "eldritch", width: int = 40):
        """
        Initialize Keeper thinking animation

        Args:
            style: Progress bar style (standard, mystical, eldritch, cosmic)
            width: Width of progress bar in characters
        """
        self.style = style if style in self.PROGRESS_BARS else "eldritch"
        self.width = width
        self.filled, self.empty = self.PROGRESS_BARS[self.style]

    def show_thinking(
        self,
        duration: float = 0.1,
        on_complete: Optional[Callable] = None
    ) -> None:
        """
        Display animated thinking state with progress bar.

        Args:
            duration: How long to animate (seconds) - actual time depends on LLM
            on_complete: Optional callback when animation completes
        """
        print()
        self._animate_progress_bar()
        if on_complete:
            on_complete()

    def _animate_progress_bar(self) -> None:
        """Animate a progress bar representing the Keeper's thinking"""
        # Calculate animation cycles
        cycles = 8
        steps_per_cycle = self.width

        for cycle in range(cycles):
            # Thinking message (rotates through frames)
            frame_idx = cycle % len(self.THINKING_FRAMES)
            thinking_msg = self.THINKING_FRAMES[frame_idx]

            # Build progress bar
            for step in range(steps_per_cycle):
                progress = (cycle * steps_per_cycle + step) / (cycles * steps_per_cycle)
                filled_count = int(progress * self.width)

                # Build bar
                bar = (
                    self.filled * filled_count +
                    self.empty * (self.width - filled_count)
                )

                # Print with carriage return (overwrite previous line)
                percentage = int(progress * 100)
                output = f"\r  ⧗ {thinking_msg:<30} [{bar}] {percentage:>3}%"
                sys.stdout.write(output)
                sys.stdout.flush()

                # Small delay for animation effect
                time.sleep(0.02)

        # Final state - complete
        print()
        print()

    def show_cosmic_hint(self, hint: Optional[str] = None) -> None:
        """
        Display a mysterious cosmic hint while thinking.

        Args:
            hint: Optional hint text about what the Keeper considers
        """
        hints = [
            "The Keeper listens to whispers from beyond...",
            "Ancient patterns emerge from the darkness...",
            "The veil between worlds grows thin...",
            "Secrets stir in the depths...",
            "Reality bends under scrutiny...",
            "The Keeper's thoughts touch strange geometries...",
        ]

        display_hint = hint or hints[int(time.time()) % len(hints)]
        print(f"\n  ✦ {display_hint}\n")

    def spinner(self, frames: Optional[list] = None, interval: float = 0.1) -> Callable:
        """
        Return a spinner function for inline animation during streaming.

        Args:
            frames: Custom spinner frames (default: spinning symbols)
            interval: Time between frames

        Returns:
            A callable that can be used as a context manager or called directly
        """
        if frames is None:
            frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        class Spinner:
            def __init__(self, frames, interval):
                self.frames = frames
                self.interval = interval
                self.current = 0

            def next(self) -> str:
                """Get next frame"""
                frame = self.frames[self.current % len(self.frames)]
                self.current += 1
                return frame

        return Spinner(frames, interval)


def print_section_divider(char: str = "━", width: int = 80) -> None:
    """Print a decorative section divider"""
    print(f"\n{char * width}\n")


def print_thinking_box(message: str, width: int = 80) -> None:
    """
    Print a message in a thinking-themed box.

    Args:
        message: Text to display
        width: Box width
    """
    padding = (width - len(message) - 4) // 2
    print(f"\n  ⧗ {' ' * padding}{message}{' ' * padding}  \n")


# Presets for common scenarios
THINKING_PRESETS = {
    "action_resolution": {
        "duration": 2.0,
        "hint": "The Keeper determines the outcome of your actions...",
    },
    "sanity_check": {
        "duration": 1.5,
        "hint": "The horror of what you witnessed settles into your mind...",
    },
    "npc_dialogue": {
        "duration": 1.0,
        "hint": "The NPC gathers their thoughts...",
    },
    "combat": {
        "duration": 2.5,
        "hint": "The Keeper unfolds the chaos of battle...",
    },
    "discovery": {
        "duration": 1.5,
        "hint": "A terrible truth begins to surface...",
    },
}


def show_keeper_thinking(
    preset: Optional[str] = None,
    custom_hint: Optional[str] = None,
    style: str = "eldritch",
) -> None:
    """
    Convenience function to show Keeper thinking with preset or custom hint.

    Args:
        preset: Preset scenario name (action_resolution, sanity_check, etc.)
        custom_hint: Custom hint text (overrides preset)
        style: Progress bar style
    """
    keeper = KeeperThinking(style=style)

    # Get hint from preset or use custom
    if custom_hint:
        hint = custom_hint
    elif preset and preset in THINKING_PRESETS:
        hint = THINKING_PRESETS[preset].get("hint")
    else:
        hint = None

    # Show cosmic hint
    if hint:
        keeper.show_cosmic_hint(hint)

    # Show thinking animation
    keeper.show_thinking()
