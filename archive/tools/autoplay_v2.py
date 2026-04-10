#!/usr/bin/env python3
"""
Auto-player v2 - with cycle detection and better exploration
"""

import sys
import json
import random
import uuid
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, '/Users/adrianmedina/src/Cthulhu')

from game_engine import CthulhuGameEngine, GameSession
from pregenerated_characters import PREGENERATED_CHARACTERS

class GameBotV2:
    def __init__(self):
        self.engine = CthulhuGameEngine()
        self.char = PREGENERATED_CHARACTERS['Eleanor']
        self.all_issues = []

    def play_session(self, strategy='random', max_steps=200):
        """Play with cycle detection"""
        session = GameSession(
            session_id=str(uuid.uuid4()),
            character=self.char,
            current_entry=1
        )

        visited = []  # Track order
        visited_set = set()
        transitions = defaultdict(list)
        choices_made = []
        issues = []

        current = 1
        steps = 0

        while steps < max_steps:
            steps += 1

            entry = self.engine.get_entry(current)
            if not entry:
                issues.append(f"Entry {current} not found")
                break

            # Validate entry
            if not entry['text'] or len(entry['text']) < 20:
                issues.append(f"Entry {current}: Text too short")

            visited.append(current)
            visited_set.add(current)

            # Check for ending
            if "THE END" in entry['text']:
                return {
                    'outcome': 'ENDING',
                    'steps': steps,
                    'visited': visited,
                    'issues': issues,
                    'transitions': dict(transitions),
                    'choices': choices_made
                }

            # No choices = dead end
            if not entry['choices']:
                return {
                    'outcome': 'DEAD_END',
                    'steps': steps,
                    'visited': visited,
                    'issues': issues,
                    'transitions': dict(transitions),
                    'choices': choices_made
                }

            # Choose next
            if len(entry['choices']) == 1 and entry['choices'][0]['text'] == '':
                # Auto-advance
                next_entry = entry['choices'][0]['destination']
            else:
                # Smart choice
                if strategy == 'explore':
                    # Prefer unvisited entries
                    best_idx = 0
                    best_score = -999
                    for i, choice in enumerate(entry['choices']):
                        dest = choice['destination']
                        score = 100 if dest not in visited_set else 0
                        score += random.random()
                        if score > best_score:
                            best_score = score
                            best_idx = i
                    next_entry = entry['choices'][best_idx]['destination']
                else:
                    # Random
                    next_entry = random.choice(entry['choices'])['destination']

            transitions[current].append(next_entry)
            choices_made.append((current, next_entry))

            # Cycle detection
            if current in visited[:-1]:  # Visited before (not just now)
                cycle_start = visited.index(current)
                cycle_entries = visited[cycle_start:]
                return {
                    'outcome': 'CYCLE',
                    'cycle_entries': cycle_entries,
                    'steps': steps,
                    'visited': visited,
                    'issues': issues,
                    'transitions': dict(transitions),
                    'choices': choices_made
                }

            current = next_entry

        return {
            'outcome': 'TIMEOUT',
            'steps': steps,
            'visited': visited,
            'issues': issues,
            'transitions': dict(transitions),
            'choices': choices_made
        }

def print_result(result, session_num):
    """Print session result"""
    print(f"\n{'─' * 70}")
    print(f"Session {session_num}: {result['outcome']} ({result['steps']} steps)")
    print(f"{'─' * 70}")

    visited = result['visited']
    print(f"Path: {' → '.join(map(str, visited[:15]))}", end='')
    if len(visited) > 15:
        print(f" ... ({len(visited)} entries)")
    else:
        print()

    # Show cycle if found
    if result['outcome'] == 'CYCLE':
        cycle = result['cycle_entries']
        print(f"⚠ CYCLE DETECTED: {cycle}")

    # Show issues
    if result['issues']:
        print(f"Issues:")
        for issue in result['issues'][:3]:
            print(f"  - {issue}")

def main():
    print("\n" + "=" * 70)
    print("  AUTOPLAY BOT v2 - EXPLORING ALL BRANCHES")
    print("=" * 70)

    bot = GameBotV2()

    print("\n[PHASE 1: Random exploration - 5 sessions]")
    for i in range(1, 6):
        result = bot.play_session(strategy='random')
        print_result(result, i)

    print("\n[PHASE 2: Smart exploration - 5 sessions]")
    for i in range(6, 11):
        result = bot.play_session(strategy='explore')
        print_result(result, i)

    print("\n" + "=" * 70)
    print("✅ VALIDATION COMPLETE")
    print("=" * 70)
    print("\nReady to identify and fix issues")
    print()

if __name__ == '__main__':
    main()
