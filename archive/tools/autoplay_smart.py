#!/usr/bin/env python3
"""
Smart autoplay bot - handles cycles intelligently, prioritizes exit choices
Runs 200 sessions for comprehensive validation
"""

import sys
import json
import random
import uuid
from collections import defaultdict

sys.path.insert(0, '/Users/adrianmedina/src/Cthulhu')

from game_engine import CthulhuGameEngine, GameSession
from pregenerated_characters import PREGENERATED_CHARACTERS

class SmartGameBotV3:
    def __init__(self):
        self.engine = CthulhuGameEngine()
        self.char = PREGENERATED_CHARACTERS['Eleanor']
        self.outcomes = defaultdict(int)
        self.path_details = []

    def play_session(self, max_steps=300, session_num=1):
        """Play with smart cycle handling"""
        session = GameSession(
            session_id=str(uuid.uuid4()),
            character=self.char,
            current_entry=1
        )

        visited = []
        visited_counts = defaultdict(int)
        choices_made = []
        current = 1
        steps = 0

        while steps < max_steps:
            steps += 1

            entry = self.engine.get_entry(current)
            if not entry:
                break

            visited.append(current)
            visited_counts[current] += 1

            # Check for ending
            if "THE END" in entry['text']:
                self.path_details.append({
                    'outcome': 'ENDING',
                    'path': visited[:],
                    'steps': steps
                })
                return {'outcome': 'ENDING', 'steps': steps, 'path': visited[:]}

            # No choices = dead end
            if not entry['choices']:
                self.path_details.append({
                    'outcome': 'DEAD_END',
                    'path': visited[:],
                    'steps': steps,
                    'location': current
                })
                return {'outcome': 'DEAD_END', 'steps': steps, 'path': visited[:]}

            # Smart choice selection
            if len(entry['choices']) == 1 and entry['choices'][0]['text'] == '':
                next_entry = entry['choices'][0]['destination']
            else:
                choice_idx = 0
                # If we've been to this entry 3+ times, prefer "leave/exit" choices
                if visited_counts[current] >= 3:
                    exit_choices = [
                        i for i, c in enumerate(entry['choices'])
                        if any(word in c['text'].lower() for word in
                              ['leave', 'exit', 'proceed', 'go', 'head', 'back', 'depart'])
                    ]
                    if exit_choices:
                        choice_idx = random.choice(exit_choices)
                    else:
                        # Take ANY unvisited destination if available
                        unvisited = [
                            i for i, c in enumerate(entry['choices'])
                            if c['destination'] not in visited_counts or visited_counts[c['destination']] == 0
                        ]
                        if unvisited:
                            choice_idx = random.choice(unvisited)
                        else:
                            choice_idx = random.randint(0, len(entry['choices']) - 1)
                else:
                    # Normal: prefer unvisited
                    best_idx = 0
                    best_score = -999
                    for i, choice in enumerate(entry['choices']):
                        dest = choice['destination']
                        # Prefer unvisited, but don't get stuck
                        score = 100 if visited_counts[dest] == 0 else (50 - visited_counts[dest] * 10)
                        score += random.random()
                        if score > best_score:
                            best_score = score
                            best_idx = i
                    choice_idx = best_idx

                next_entry = entry['choices'][choice_idx]['destination']
            choices_made.append((current, next_entry))
            current = next_entry

        # Timeout
        self.path_details.append({
            'outcome': 'TIMEOUT',
            'path': visited[:],
            'steps': steps
        })
        return {'outcome': 'TIMEOUT', 'steps': steps, 'path': visited[:]}

def main():
    print("\n" + "=" * 80)
    print("  SMART AUTOPLAY BOT v3 - 200 SESSION VALIDATION")
    print("  (with intelligent cycle handling)")
    print("=" * 80)

    bot = SmartGameBotV3()
    num_sessions = 200

    print(f"\nRunning {num_sessions} automated game sessions...\n")

    for session_num in range(1, num_sessions + 1):
        result = bot.play_session(session_num=session_num)
        bot.outcomes[result['outcome']] += 1

        if session_num % 20 == 0:
            outcomes_so_far = dict(bot.outcomes)
            print(f"  {session_num}/{num_sessions} - "
                  f"Endings: {outcomes_so_far.get('ENDING', 0)} | "
                  f"Dead: {outcomes_so_far.get('DEAD_END', 0)} | "
                  f"Timeout: {outcomes_so_far.get('TIMEOUT', 0)}")

    # Final stats
    print(f"\n\n{'=' * 80}")
    print("  FINAL VALIDATION REPORT")
    print(f"{'=' * 80}\n")

    print("OUTCOMES:")
    for outcome in ['ENDING', 'DEAD_END', 'TIMEOUT']:
        count = bot.outcomes[outcome]
        pct = (count / num_sessions) * 100
        print(f"  {outcome:12s}: {count:3d} sessions ({pct:5.1f}%)")

    endings = bot.outcomes['ENDING']
    print(f"\n✅ Success Rate: {endings}/{num_sessions} ({(endings/num_sessions)*100:.1f}%)")

    # Unique winning paths
    winning_paths = defaultdict(int)
    for detail in bot.path_details:
        if detail['outcome'] == 'ENDING':
            path = tuple(detail['path'])
            winning_paths[path] += 1

    print(f"\n📍 UNIQUE WINNING PATHS: {len(winning_paths)}")
    for i, (path, count) in enumerate(sorted(winning_paths.items(), key=lambda x: -x[1])[:5], 1):
        path_str = '→'.join(map(str, list(path)[:12]))
        if len(path) > 12:
            path_str += f"...({len(path)} steps)"
        print(f"  {i}. {path_str}")
        print(f"     {count} sessions ({(count/endings)*100:.1f}% of endings)")

    if endings == num_sessions:
        print(f"\n{'=' * 80}")
        print("🎉 STATUS: 100% SUCCESS RATE - GAME IS FULLY PLAYABLE")
        print(f"{'=' * 80}\n")
    elif endings >= (num_sessions * 0.90):
        print(f"\n{'=' * 80}")
        print(f"✅ STATUS: {(endings/num_sessions)*100:.1f}% SUCCESS RATE - EXCELLENT")
        print(f"{'=' * 80}\n")
    elif endings >= (num_sessions * 0.75):
        print(f"\n{'=' * 80}")
        print(f"⚠️  STATUS: {(endings/num_sessions)*100:.1f}% SUCCESS RATE - GOOD")
        print(f"{'=' * 80}\n")

if __name__ == '__main__':
    main()
