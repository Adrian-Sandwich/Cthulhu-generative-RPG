"""Tests for terminal input handling in the history viewer."""

import io

from ui import history_viewer


def test_getch_reads_first_character_from_redirected_stdin(monkeypatch):
    """A redirected stream should use line-buffered input instead of raw mode."""
    monkeypatch.setattr(history_viewer.sys, "stdin", io.StringIO("j\n"))

    assert history_viewer._getch() == "j"


def test_getch_returns_quit_at_end_of_redirected_stdin(monkeypatch):
    """EOF on redirected stdin should safely leave the interactive pager."""
    monkeypatch.setattr(history_viewer.sys, "stdin", io.StringIO(""))

    assert history_viewer._getch() == "q"
