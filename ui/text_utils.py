#!/usr/bin/env python3
"""Shared text helpers for the terminal UI (single source for word-wrap)."""

from typing import List


def wrap_text(text: str, width: int) -> List[str]:
    """
    Wrap text to fit width, breaking on words.

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
