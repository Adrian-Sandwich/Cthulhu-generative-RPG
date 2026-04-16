#!/usr/bin/env python3
"""
Terminal Color System for Call of Cthulhu Retro UI
Detects terminal capabilities and provides color utilities with fallback
"""

import os
import sys
from enum import Enum
from typing import Optional, Tuple


class ColorMode(Enum):
    """Supported color modes"""
    FULL_256 = "256color"    # Full 256-color support
    ANSI_16 = "16color"      # Basic 16-color ANSI
    MONOCHROME = "mono"      # No color support


class TerminalColors:
    """ANSI color codes and utilities for terminal output"""

    # Primary palette (256-color codes)
    COLORS_256 = {
        "orange": 208,        # Orange/Amber
        "green": 46,          # Neon Green
        "cyan": 51,           # Bright Cyan
        "black": 0,           # Black background
        "white": 15,          # White text
        "gray": 8,            # Dark gray
        "yellow": 11,         # Yellow
        "red": 9,             # Red
    }

    # Fallback ANSI 16 colors
    COLORS_16 = {
        "orange": "33",       # Bright Yellow (closest to orange)
        "green": "32",        # Green
        "cyan": "36",         # Cyan
        "black": "40",        # Black background
        "white": "37",        # White
        "gray": "90",         # Bright Black
        "yellow": "33",       # Yellow
        "red": "31",          # Red
    }

    def __init__(self, mode: Optional[ColorMode] = None, force_mono: bool = False):
        """
        Initialize color system.

        Args:
            mode: Force a specific color mode (auto-detect if None)
            force_mono: Force monochrome mode (for testing)
        """
        self.force_mono = force_mono
        self.mode = mode or self._detect_color_mode()

        # Disable color if CLICOLOR_FORCE=0 or NO_COLOR set
        if os.environ.get('CLICOLOR_FORCE') == '0' or os.environ.get('NO_COLOR'):
            self.mode = ColorMode.MONOCHROME

    def _detect_color_mode(self) -> ColorMode:
        """
        Detect terminal color capabilities.

        Returns:
            ColorMode indicating what the terminal supports
        """
        # Check environment variables first
        term = os.environ.get('TERM', '').lower()
        colorterm = os.environ.get('COLORTERM', '').lower()

        # Check for 256-color support
        if '256color' in term or 'truecolor' in colorterm:
            return ColorMode.FULL_256

        # Check for basic color support
        if any(x in term for x in ['color', 'xterm', 'linux', 'screen']):
            return ColorMode.ANSI_16

        # Default to monochrome
        return ColorMode.MONOCHROME

    def colorize(
        self,
        text: str,
        color: str = "white",
        bold: bool = False,
        bg: Optional[str] = None
    ) -> str:
        """
        Apply color to text.

        Args:
            text: Text to colorize
            color: Color name (orange, green, cyan, white, red, yellow, etc.)
            bold: Make text bold
            bg: Background color name

        Returns:
            Colored text (or plain text if monochrome)
        """
        if self.force_mono or self.mode == ColorMode.MONOCHROME:
            return text

        if self.mode == ColorMode.FULL_256:
            return self._colorize_256(text, color, bold, bg)
        else:
            return self._colorize_16(text, color, bold, bg)

    def _colorize_256(
        self,
        text: str,
        color: str,
        bold: bool,
        bg: Optional[str]
    ) -> str:
        """Apply 256-color ANSI codes"""
        codes = []

        # Foreground color
        color_code = self.COLORS_256.get(color, 15)
        codes.append(f"38;5;{color_code}")

        # Bold
        if bold:
            codes.insert(0, "1")

        # Background color
        if bg:
            bg_code = self.COLORS_256.get(bg, 0)
            codes.append(f"48;5;{bg_code}")

        code_str = ";".join(codes)
        return f"\033[{code_str}m{text}\033[0m"

    def _colorize_16(
        self,
        text: str,
        color: str,
        bold: bool,
        bg: Optional[str]
    ) -> str:
        """Apply 16-color ANSI codes (fallback)"""
        codes = []

        # Foreground color
        color_code = self.COLORS_16.get(color, "37")
        codes.append(color_code)

        # Bold
        if bold:
            codes.insert(0, "1")

        # Background color
        if bg:
            bg_code = self.COLORS_16.get(bg, "40")
            codes.append(bg_code)

        code_str = ";".join(codes)
        return f"\033[{code_str}m{text}\033[0m"

    def reset(self) -> str:
        """Return ANSI reset code"""
        if self.mode == ColorMode.MONOCHROME:
            return ""
        return "\033[0m"

    def clear_line(self) -> str:
        """Return ANSI clear line code"""
        return "\033[2K"

    def move_cursor(self, row: int, col: int) -> str:
        """Return ANSI code to move cursor"""
        return f"\033[{row};{col}H"

    def hide_cursor(self) -> str:
        """Hide terminal cursor"""
        return "\033[?25h"

    def show_cursor(self) -> str:
        """Show terminal cursor"""
        return "\033[?25l"

    # Convenience methods
    def orange(self, text: str, bold: bool = False) -> str:
        """Orange/amber text"""
        return self.colorize(text, "orange", bold=bold)

    def green(self, text: str, bold: bool = False) -> str:
        """Green text"""
        return self.colorize(text, "green", bold=bold)

    def cyan(self, text: str, bold: bool = False) -> str:
        """Cyan text"""
        return self.colorize(text, "cyan", bold=bold)

    def red(self, text: str, bold: bool = False) -> str:
        """Red text (for warnings/errors)"""
        return self.colorize(text, "red", bold=bold)

    def yellow(self, text: str, bold: bool = False) -> str:
        """Yellow text"""
        return self.colorize(text, "yellow", bold=bold)

    def gray(self, text: str) -> str:
        """Gray text (for secondary info)"""
        return self.colorize(text, "gray")

    def white(self, text: str, bold: bool = False) -> str:
        """White text"""
        return self.colorize(text, "white", bold=bold)


# Global color instance (can be overridden for testing)
_global_colors: Optional[TerminalColors] = None


def get_colors(force_mono: bool = False) -> TerminalColors:
    """
    Get or create global color instance.

    Args:
        force_mono: Force monochrome mode

    Returns:
        TerminalColors instance
    """
    global _global_colors
    if _global_colors is None:
        _global_colors = TerminalColors(force_mono=force_mono)
    return _global_colors


def detect_mode() -> ColorMode:
    """Get detected terminal color mode"""
    return get_colors().mode


def is_color_supported() -> bool:
    """Check if colors are supported"""
    return get_colors().mode != ColorMode.MONOCHROME


# Utility function for quick colorization
def colorize(text: str, color: str = "white", bold: bool = False) -> str:
    """Quick colorize function using global instance"""
    return get_colors().colorize(text, color, bold=bold)


def orange(text: str, bold: bool = False) -> str:
    """Quick orange colorize"""
    return get_colors().orange(text, bold=bold)


def green(text: str, bold: bool = False) -> str:
    """Quick green colorize"""
    return get_colors().green(text, bold=bold)


def cyan(text: str, bold: bool = False) -> str:
    """Quick cyan colorize"""
    return get_colors().cyan(text, bold=bold)


def red(text: str, bold: bool = False) -> str:
    """Quick red colorize"""
    return get_colors().red(text, bold=bold)


def yellow(text: str, bold: bool = False) -> str:
    """Quick yellow colorize"""
    return get_colors().yellow(text, bold=bold)


def gray(text: str) -> str:
    """Quick gray colorize"""
    return get_colors().gray(text)


def white(text: str, bold: bool = False) -> str:
    """Quick white colorize"""
    return get_colors().white(text, bold=bold)


# Test function
if __name__ == "__main__":
    print("Color System Test")
    print("=" * 60)

    colors = TerminalColors()
    print(f"Detected mode: {colors.mode.value}")
    print()

    print(colors.orange("Orange text"))
    print(colors.green("Green text"))
    print(colors.cyan("Cyan text"))
    print(colors.red("Red text"))
    print(colors.yellow("Yellow text"))
    print(colors.gray("Gray text"))
    print(colors.white("White text", bold=True))

    print()
    print("Monochrome mode test:")
    mono_colors = TerminalColors(force_mono=True)
    print(mono_colors.orange("This looks like normal text in monochrome"))
