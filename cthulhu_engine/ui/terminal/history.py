#!/usr/bin/env python3
"""
History Viewer - Display complete game history
Shows all turns, discoveries, decisions made
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional
import re
import tty
import termios
from ui.color_system import orange, green, cyan, red, yellow, gray
from ui.retro_display import RetroDisplay

# ANSI escape code regex for measuring visual length
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def _visual_len(s: str) -> int:
    """Measure printable length of string, ignoring ANSI escape codes."""
    return len(_ANSI_RE.sub('', s))


def _getch() -> str:
    """Read one keypress in raw mode (no echo). Returns char or arrow escape sequence."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)   # '['
            ch3 = sys.stdin.read(1)   # A/B/C/D for arrows
            return '\x1b' + ch2 + ch3
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


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

    def _build_history_lines(
        self, narrative_turns: List[str], investigator_name: str, location: str, turn: int,
        discoveries: List[str] = None, stats: Dict = None
    ) -> List[str]:
        """Build list of pre-rendered (colored) lines for the interactive pager."""
        lines = []

        # Header
        lines.append(orange("═" * self.width, bold=True))
        lines.append(orange(f"GAME HISTORY: {investigator_name}".center(self.width), bold=True))
        lines.append(orange(f"Turn {turn} | Location: {location}".center(self.width)))
        lines.append(orange("═" * self.width, bold=True))
        lines.append("")

        # Stats
        if stats:
            lines.append(cyan("CURRENT STATE:", bold=True))
            for key, value in stats.items():
                if isinstance(value, tuple):
                    lines.append(f"  {key}: {value[0]}/{value[1]}")
                else:
                    lines.append(f"  {key}: {value}")
            lines.append("")

        # Discoveries
        if discoveries:
            lines.append(green("DISCOVERIES:", bold=True))
            for i, d in enumerate(discoveries, 1):
                lines.append(f"  {i}. {d}")
            lines.append("")

        # Narrative
        lines.append(cyan("COMPLETE NARRATIVE:", bold=True))
        lines.append(gray("─" * self.width))
        lines.append("")

        for i, turn_text in enumerate(narrative_turns, 1):
            if turn_text.startswith("Player:"):
                action = turn_text.replace("Player: ", "")
                prefix = yellow(f"[Turn {i}] ")
                content_lines = self._wrap_text(action, self.width - 4)
                if content_lines:
                    lines.append(f"  {prefix}{green(content_lines[0], bold=True)}")
                    for cont in content_lines[1:]:
                        lines.append(f"          {green(cont, bold=True)}")
            elif turn_text.startswith("DM:"):
                narration = turn_text.replace("DM: ", "")
                prefix = yellow(f"[Turn {i}] ")
                content_lines = self._wrap_text(narration, self.width - 4)
                if content_lines:
                    lines.append(f"  {prefix}{cyan(content_lines[0])}")
                    for cont in content_lines[1:]:
                        lines.append(f"          {cyan(cont)}")
            else:
                content_lines = self._wrap_text(turn_text, self.width - 4)
                if content_lines:
                    lines.append(f"  {yellow(f'[Turn {i}] ')}{content_lines[0]}")
                    for cont in content_lines[1:]:
                        lines.append(f"          {cont}")
            lines.append("")

        lines.append(gray("─" * self.width))
        return lines

    def _run_pager(self, lines: List[str]) -> None:
        """Interactive pager: arrow keys scroll, / searches, q quits."""
        try:
            term_h, term_w = os.get_terminal_size()
        except OSError:
            term_h, term_w = 24, 80

        view_h = term_h - 2  # reserve 2 rows for status bar
        max_top = max(0, len(lines) - view_h)
        top = 0
        search_term = ''
        search_mode = False
        search_results: List[int] = []
        result_idx = 0

        def render():
            sys.stdout.write('\033[H')  # cursor home

            # Draw visible lines
            for i in range(view_h):
                row = i + 1
                li = top + i
                sys.stdout.write(f'\033[{row};1H\033[2K')  # move and erase line

                if li < len(lines):
                    line = lines[li]
                    # Truncate to terminal width
                    visual = _ANSI_RE.sub('', line)
                    if len(visual) > term_w:
                        # Find byte position that matches term_w visible chars
                        chars = 0
                        byte_pos = 0
                        i_c = 0
                        while i_c < len(line) and chars < term_w:
                            if line[i_c:].startswith('\x1b'):
                                end = line.find('m', i_c)
                                byte_pos = end + 1
                                i_c = byte_pos
                            else:
                                chars += 1
                                i_c += 1
                                byte_pos = i_c
                        line = line[:byte_pos]

                    # Highlight search matches
                    if search_term:
                        plain = _ANSI_RE.sub('', line)
                        if search_term.lower() in plain.lower():
                            idx = plain.lower().find(search_term.lower())
                            line = (plain[:idx]
                                    + f'\033[7m{plain[idx:idx+len(search_term)]}\033[0m'
                                    + plain[idx+len(search_term):])

                    sys.stdout.write(line)

            # Status bar
            pct = int(min(100, (top / max(1, max_top)) * 100)) if max_top else 100
            match_info = f'  [{result_idx+1}/{len(search_results)}]' if search_results else ''

            if search_mode:
                status = f'  SEARCH: {search_term}_   ESC=cancel  ENTER=jump'
            else:
                status = (f'  ↑↓/jk scroll  SPACE/b page  /=search  '
                          f'n/N match{match_info}  g=top  G=end  q=quit  '
                          f'[{top+1}-{min(top+view_h, len(lines))}/{len(lines)}] {pct}%')

            sys.stdout.write(f'\033[{term_h-1};1H\033[2K\033[7m{status[:term_w].ljust(term_w)}\033[0m')
            sys.stdout.flush()

        sys.stdout.write('\033[?25l\033[2J\033[H')  # hide cursor, clear screen

        try:
            while True:
                render()
                key = _getch()

                if search_mode:
                    if key in ('\r', '\n'):
                        search_mode = False
                        if search_results:
                            top = min(search_results[result_idx], max_top)
                    elif key == '\x1b':
                        search_mode = False
                        search_term = ''
                        search_results = []
                    elif key == '\x7f':  # backspace
                        search_term = search_term[:-1]
                        search_results = [i for i, ln in enumerate(lines)
                                          if search_term and search_term.lower() in _ANSI_RE.sub('', ln).lower()]
                        result_idx = 0
                        if search_results:
                            top = min(search_results[0], max_top)
                    else:
                        search_term += key
                        search_results = [i for i, ln in enumerate(lines)
                                          if search_term.lower() in _ANSI_RE.sub('', ln).lower()]
                        result_idx = 0
                        if search_results:
                            top = min(search_results[0], max_top)
                    continue

                # Normal mode navigation
                if key in ('q', 'Q', '\x03', '\x04'):  # q or Ctrl-C/D
                    break
                elif key in ('\x1b[A', 'k', 'K'):  # UP arrow or k
                    top = max(0, top - 1)
                elif key in ('\x1b[B', 'j', 'J'):  # DOWN arrow or j
                    top = min(max_top, top + 1)
                elif key in (' ', '\x1b[6~'):  # SPACE or Page Down
                    top = min(max_top, top + view_h)
                elif key in ('b', 'B', '\x1b[5~'):  # b or Page Up
                    top = max(0, top - view_h)
                elif key == 'g':  # go to top
                    top = 0
                elif key == 'G':  # go to bottom
                    top = max_top
                elif key == '/':  # enter search
                    search_mode = True
                    search_term = ''
                    search_results = []
                elif key == 'n' and search_results:  # next match
                    result_idx = (result_idx + 1) % len(search_results)
                    top = min(search_results[result_idx], max_top)
                elif key == 'N' and search_results:  # prev match
                    result_idx = (result_idx - 1) % len(search_results)
                    top = min(search_results[result_idx], max_top)

        finally:
            sys.stdout.write('\033[?25h\033[2J\033[H')  # show cursor, clear
            sys.stdout.flush()

    def display_scrollable(
        self, narrative_turns: List[str], investigator_name: str, location: str, turn: int,
        discoveries: List[str] = None, stats: Dict = None
    ) -> None:
        """Display full game history in an interactive scrollable pager."""
        lines = self._build_history_lines(narrative_turns, investigator_name, location, turn, discoveries, stats)
        self._run_pager(lines)

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
