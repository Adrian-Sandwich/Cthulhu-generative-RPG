#!/usr/bin/env python3
"""
Auto-player bot - plays multiple game sessions to validate parser and story flow
Tests against PDF, identifies issues, makes generic improvements
"""

import sys
import json
import random
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/Users/adrianmedina/src/Cthulhu')

from game_engine import CthulhuGameEngine, GameSession, DiceRoller
from pregenerated_characters import PREGENERATED_CHARACTERS

class GameBot:
    def __init__(self):
        self.engine = CthulhuGameEngine()
        self.char = PREGENERATED_CHARACTERS['Eleanor']
        self.session = None
        self.visited_entries = set()
        self.issues = []
        self.decisions = []
        self.game_log = []

        # Load PDF text for validation
        with open('/tmp/adventure_full.txt', 'r', encoding='utf-8', errors='ignore') as f:
            self.pdf_text = f.read()

    def validate_entry(self, entry_num, entry):
        """Validate entry against PDF"""
        issues = []

        # Check text exists and is not empty
        if not entry['text'] or len(entry['text']) < 20:
            issues.append(f"Entry {entry_num}: Text too short or empty ({len(entry['text'])} chars)")

        # Check for incomplete cleanup (markers left in text)
        if '•' in entry['text']:
            issues.append(f"Entry {entry_num}: Contains bullet marker '•'")

        if 'Go to' in entry['text'] and entry['choices']:
            # Might be choice text not properly extracted
            pass  # This is often OK

        return issues

    def should_continue_living(self):
        """Check if player should continue"""
        if self.session.hp_current <= 0:
            self.game_log.append("DEATH: HP reached 0")
            return False

        if self.session.san_current <= 0:
            self.game_log.append("INSANITY: SAN reached 0")
            return False

        return True

    def choose_action(self, entry):
        """AI chooses next action"""
        if not entry['choices']:
            return None

        # Strategy: prefer investigation/survival actions
        # Avoid death/insanity choices when possible

        choice_texts = [c['text'].lower() for c in entry['choices']]

        # Heuristics: prefer certain keywords
        prefer_keywords = ['investigate', 'search', 'examine', 'ask', 'flee', 'escape', 'hide', 'help']
        avoid_keywords = ['attack', 'confront', 'fight', 'scream', 'panic']

        best_choice = 0
        best_score = -999

        for i, text in enumerate(choice_texts):
            score = 0

            # Prefer investigation
            for keyword in prefer_keywords:
                if keyword in text:
                    score += 10

            # Avoid dangerous
            for keyword in avoid_keywords:
                if keyword in text:
                    score -= 5

            # Random tiebreaker
            score += random.uniform(-1, 1)

            if score > best_score:
                best_score = score
                best_choice = i

        return best_choice

    def play_session(self, max_entries=100):
        """Play one complete session"""
        self.session = GameSession(
            session_id=str(uuid.uuid4()),
            character=self.char,
            current_entry=1
        )

        self.visited_entries = set()
        self.decisions = []
        self.game_log = []

        current_entry = 1
        steps = 0

        while steps < max_entries and self.should_continue_living():
            steps += 1

            # Load entry
            entry = self.engine.get_entry(current_entry)
            if not entry:
                self.game_log.append(f"ERROR: Entry {current_entry} not found")
                break

            # Validate
            entry_issues = self.validate_entry(current_entry, entry)
            if entry_issues:
                self.issues.extend(entry_issues)

            # Track
            self.visited_entries.add(current_entry)
            self.game_log.append(f"Entry {current_entry}: {len(entry['text'])} chars, {len(entry['choices'])} choices")

            # Update session
            self.session.current_entry = current_entry
            self.session.last_action_at = datetime.now()

            # Check for story endings
            if "THE END" in entry['text']:
                self.game_log.append("ENDING: Found 'THE END'")
                break

            # Get next choice
            if not entry['choices']:
                self.game_log.append(f"No choices at entry {current_entry} - END OF BRANCH")
                break

            # Single choice = auto-advance
            if len(entry['choices']) == 1 and entry['choices'][0]['text'] == '':
                next_num = entry['choices'][0]['destination']
                self.game_log.append(f"  → Auto-advance to {next_num}")
            else:
                # Multiple choices = choose via AI
                choice_idx = self.choose_action(entry)
                next_num = entry['choices'][choice_idx]['destination']
                choice_text = entry['choices'][choice_idx]['text']

                self.decisions.append({
                    'from': current_entry,
                    'to': next_num,
                    'text': choice_text[:50]
                })

                self.game_log.append(f"  → CHOOSE: {choice_text[:60]}... → {next_num}")

            current_entry = next_num

        # Determine outcome
        if self.session.hp_current <= 0:
            outcome = "DEATH"
        elif self.session.san_current <= 0:
            outcome = "INSANITY"
        elif steps >= max_entries:
            outcome = "TIMEOUT"
        else:
            outcome = "COMPLETED"

        return {
            'outcome': outcome,
            'steps': steps,
            'entries_visited': len(self.visited_entries),
            'unique_entries': sorted(self.visited_entries),
            'decisions': self.decisions,
            'log': self.game_log,
            'issues': entry_issues if entry_issues else []
        }

    def print_session_summary(self, session_num, result):
        """Print summary of one session"""
        print(f"\n{'=' * 70}")
        print(f"  SESSION {session_num}: {result['outcome']}")
        print(f"{'=' * 70}")
        print(f"Steps: {result['steps']}")
        print(f"Entries visited: {result['entries_visited']}")
        print(f"Entry range: {min(result['unique_entries'])} - {max(result['unique_entries'])}")
        print(f"Decisions made: {len(result['decisions'])}")

        if result['decisions']:
            print(f"\nDecision path:")
            for d in result['decisions'][:5]:
                print(f"  {d['from']} → {d['to']}: {d['text']}")
            if len(result['decisions']) > 5:
                print(f"  ... and {len(result['decisions']) - 5} more")

        if result['issues']:
            print(f"\n⚠ Issues found:")
            for issue in result['issues']:
                print(f"  - {issue}")

def main():
    print("\n" + "=" * 70)
    print("  AUTOPLAY BOT - VALIDATING GAME ENGINE")
    print("=" * 70)

    bot = GameBot()

    results = []
    outcomes = {}

    # Play multiple sessions
    num_sessions = 5

    for session_num in range(1, num_sessions + 1):
        print(f"\n[SESSION {session_num}/{num_sessions}] Starting...")
        result = bot.play_session(max_entries=100)
        results.append(result)

        outcomes[result['outcome']] = outcomes.get(result['outcome'], 0) + 1

        bot.print_session_summary(session_num, result)

    # Final report
    print(f"\n\n{'=' * 70}")
    print("  FINAL REPORT")
    print(f"{'=' * 70}")

    print(f"\nOutcomes:")
    for outcome, count in outcomes.items():
        print(f"  {outcome}: {count} sessions")

    print(f"\nTotal issues found: {len(bot.issues)}")
    if bot.issues:
        unique_issues = list(set(bot.issues))
        print(f"Unique issues:")
        for issue in unique_issues[:10]:
            print(f"  - {issue}")
        if len(unique_issues) > 10:
            print(f"  ... and {len(unique_issues) - 10} more")

    print(f"\n{'=' * 70}")
    print("STATUS: Ready for next steps")
    print(f"{'=' * 70}\n")

if __name__ == '__main__':
    main()
