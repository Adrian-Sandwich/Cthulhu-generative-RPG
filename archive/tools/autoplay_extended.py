#!/usr/bin/env python3
"""
Extended autoplay bot - runs 200 sessions for comprehensive validation
Tracks detailed statistics and identifies any remaining issues
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

class ExtendedGameBotV2:
    def __init__(self):
        self.engine = CthulhuGameEngine()
        self.char = PREGENERATED_CHARACTERS['Eleanor']
        self.all_issues = []
        self.outcomes = defaultdict(int)
        self.paths = defaultdict(int)
        self.path_details = []
        self.dead_ends = []
        self.cycles = []

    def play_session(self, strategy='random', max_steps=200, session_num=1):
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
                issues.append(f"Entry {current}: Text too short ({len(entry['text'])} chars)")

            visited.append(current)
            visited_set.add(current)

            # Check for ending
            if "THE END" in entry['text']:
                path_str = ' → '.join(map(str, visited))
                self.paths[path_str] += 1
                self.path_details.append({
                    'session': session_num,
                    'path': visited[:],
                    'steps': steps,
                    'outcome': 'ENDING'
                })
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
                self.dead_ends.append({'entry': current, 'session': session_num, 'path': visited[:]})
                self.path_details.append({
                    'session': session_num,
                    'path': visited[:],
                    'steps': steps,
                    'outcome': 'DEAD_END',
                    'dead_end_at': current
                })
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
                cycle_str = '→'.join(map(str, cycle_entries))
                self.cycles.append({'cycle': cycle_str, 'session': session_num})
                self.path_details.append({
                    'session': session_num,
                    'path': visited[:],
                    'steps': steps,
                    'outcome': 'CYCLE',
                    'cycle': cycle_entries
                })
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

def main():
    print("\n" + "=" * 80)
    print("  EXTENDED AUTOPLAY BOT - 200 SESSION COMPREHENSIVE VALIDATION")
    print("=" * 80)

    bot = ExtendedGameBotV2()
    num_sessions = 200

    # Progress bar
    print(f"\nRunning {num_sessions} automated game sessions...\n")

    for session_num in range(1, num_sessions + 1):
        # Alternate strategies
        strategy = 'random' if session_num % 2 == 0 else 'explore'
        result = bot.play_session(strategy=strategy, session_num=session_num)

        bot.outcomes[result['outcome']] += 1

        # Progress indicator every 20 sessions
        if session_num % 20 == 0:
            outcomes_so_far = dict(bot.outcomes)
            print(f"  {session_num}/{num_sessions} sessions complete - "
                  f"Endings: {outcomes_so_far.get('ENDING', 0)} | "
                  f"Dead Ends: {outcomes_so_far.get('DEAD_END', 0)} | "
                  f"Cycles: {outcomes_so_far.get('CYCLE', 0)} | "
                  f"Timeouts: {outcomes_so_far.get('TIMEOUT', 0)}")

    # Final report
    print(f"\n\n{'=' * 80}")
    print("  FINAL REPORT - 200 SESSION VALIDATION")
    print(f"{'=' * 80}\n")

    print("OUTCOMES:")
    for outcome in ['ENDING', 'DEAD_END', 'CYCLE', 'TIMEOUT']:
        count = bot.outcomes[outcome]
        pct = (count / num_sessions) * 100
        print(f"  {outcome:12s}: {count:3d} sessions ({pct:5.1f}%)")

    total_endings = bot.outcomes['ENDING']
    print(f"\n✅ Success Rate: {total_endings}/{num_sessions} ({(total_endings/num_sessions)*100:.1f}%)")

    if bot.dead_ends:
        print(f"\n⚠️  DEAD ENDS FOUND: {len(set(d['entry'] for d in bot.dead_ends))} unique locations")
        dead_end_entries = defaultdict(int)
        for d in bot.dead_ends:
            dead_end_entries[d['entry']] += 1
        print("  Most common dead ends:")
        for entry, count in sorted(dead_end_entries.items(), key=lambda x: -x[1])[:5]:
            print(f"    - Entry {entry}: {count} sessions")

    if bot.cycles:
        print(f"\n🔄 CYCLES DETECTED: {len(set(c['cycle'] for c in bot.cycles))} unique patterns")
        cycle_patterns = defaultdict(int)
        for c in bot.cycles:
            cycle_patterns[c['cycle']] += 1
        print("  Cycle patterns:")
        for cycle, count in sorted(cycle_patterns.items(), key=lambda x: -x[1])[:5]:
            print(f"    - {cycle}: {count} sessions")

    # Find unique paths to success
    winning_paths = defaultdict(int)
    for detail in bot.path_details:
        if detail['outcome'] == 'ENDING':
            path = tuple(detail['path'])
            winning_paths[path] += 1

    print(f"\n📍 UNIQUE WINNING PATHS: {len(winning_paths)}")
    for i, (path, count) in enumerate(sorted(winning_paths.items(), key=lambda x: -x[1])[:5], 1):
        path_str = '→'.join(map(str, list(path)[:10]))
        if len(path) > 10:
            path_str += f"...({len(path)} total)"
        print(f"  {i}. {path_str}")
        print(f"     Frequency: {count} sessions ({(count/total_endings)*100:.1f}% of endings)")

    print(f"\n{'=' * 80}")
    if total_endings == num_sessions:
        print("✅ STATUS: ALL SESSIONS REACH ENDINGS - GAME IS PRODUCTION READY")
    elif total_endings >= (num_sessions * 0.95):
        print(f"✅ STATUS: {(total_endings/num_sessions)*100:.1f}% SUCCESS RATE - EXCELLENT")
    elif total_endings >= (num_sessions * 0.80):
        print(f"⚠️  STATUS: {(total_endings/num_sessions)*100:.1f}% SUCCESS RATE - GOOD (minor fixes needed)")
    else:
        print(f"❌ STATUS: {(total_endings/num_sessions)*100:.1f}% SUCCESS RATE - NEEDS WORK")
    print(f"{'=' * 80}\n")

if __name__ == '__main__':
    main()
