"""
UI components for Call of Cthulhu generative game engine
"""

from .keeper_thinking import (
    KeeperThinking,
    show_keeper_thinking,
    print_section_divider,
    print_thinking_box,
    THINKING_PRESETS,
)

from .color_system import (
    TerminalColors,
    ColorMode,
    get_colors,
    detect_mode,
    is_color_supported,
    colorize,
    orange,
    green,
    cyan,
    red,
    yellow,
    gray,
    white,
)

from .retro_display import (
    RetroDisplay,
    GameStateDisplay,
    NarrativeDisplay,
    InventoryDisplay,
    DialogueDisplay,
    EndingDisplay,
)

from .game_display import (
    GameDisplayManager,
)

__all__ = [
    # Keeper Thinking
    "KeeperThinking",
    "show_keeper_thinking",
    "print_section_divider",
    "print_thinking_box",
    "THINKING_PRESETS",
    # Colors
    "TerminalColors",
    "ColorMode",
    "get_colors",
    "detect_mode",
    "is_color_supported",
    "colorize",
    "orange",
    "green",
    "cyan",
    "red",
    "yellow",
    "gray",
    "white",
    # Display
    "RetroDisplay",
    "GameStateDisplay",
    "NarrativeDisplay",
    "InventoryDisplay",
    "DialogueDisplay",
    "EndingDisplay",
    # Game Display Manager
    "GameDisplayManager",
]
