"""Tests for terminal input handling in the history viewer."""

import io
import sys
from types import SimpleNamespace

from ui import history_viewer


def test_getch_reads_first_character_from_redirected_stdin(monkeypatch):
    """A redirected stream should use line-buffered input instead of raw mode."""
    monkeypatch.setattr(history_viewer.sys, "stdin", io.StringIO("j\n"))

    assert history_viewer._getch() == "j"


def test_getch_returns_quit_at_end_of_redirected_stdin(monkeypatch):
    """EOF on redirected stdin should safely leave the interactive pager."""
    monkeypatch.setattr(history_viewer.sys, "stdin", io.StringIO(""))

    assert history_viewer._getch() == "q"


def test_getch_translates_windows_arrow_keys(monkeypatch):
    """Windows console arrow prefixes should become POSIX escape sequences."""
    monkeypatch.setattr(history_viewer.os, "name", "nt")
    monkeypatch.setattr(history_viewer.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    # A queue is needed because getch is called once for the prefix and once
    # for the arrow code.
    keys = iter((b"\xe0", b"M"))
    msvcrt = SimpleNamespace(getch=lambda: next(keys))
    monkeypatch.setitem(sys.modules, "msvcrt", msvcrt)

    assert history_viewer._getch() == "\x1b[C"
