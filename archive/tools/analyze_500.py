#!/usr/bin/env python3
"""
Comprehensive game analysis - 500 automated playthroughs
Validates logic, continuity, parsing, and game mechanics
"""

import sys
import json
import random
import uuid
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, '/Users/adrianmedina/src/Cthulhu')

from game_engine import CthulhuGameEngine, GameSession, DiceRoller
from pregenerated_characters import PREGENERATED_CHARACTERS

class ComprehensiveGameAnalyzer:
    def __init__(self):
        self.engine = CthulhuGameEngine()
        self.char = PREGENERATED_CHARACTERS['Eleanor']

        # Tracking
        self.outcomes = defaultdict(int)
        self.errors = []
        self.logic_issues = []
        self.parsing_issues = []
        self.continuity_issues = []
        self.dynamic_issues = []
        self.skill_issues = []
        self.all_paths = []
        self.roll_outcomes = defaultdict(int)

    def validate_entry(self, entry_num, entry):
        """Validate entry structure and content"""
        issues = []

        # Check text exists and is reasonable
        if not entry.get('text'):
            issues.append(f"Entry {entry_num}: Missing text")
        elif len(entry['text']) < 10:
            issues.append(f"Entry {entry_num}: Text too short ({len(entry['text'])} chars)")

        # Check for orphaned markup
        text = entry.get('text', '')
        if '•' in text and text.count('go to') > 0:
            issues.append(f"Entry {entry_num}: Contains orphaned choice markup")

        if ';;' in text or '...' in text:
            issues.append(f"Entry {entry_num}: Suspicious punctuation/formatting")

        # Validate choices
        for i, choice in enumerate(entry.get('choices', [])):
            if 'destination' not in choice:
                issues.append(f"Entry {entry_num}: Choice {i} missing destination")

            dest = choice.get('destination')
            if dest and not isinstance(dest, int):
                issues.append(f"Entry {entry_num}: Choice {i} destination not integer")

            # Check if destination exists
            if dest and not (1 <= dest <= 243):
                issues.append(f"Entry {entry_num}: Choice {i} references invalid entry {dest}")

        # Check for roll metadata integrity
        if entry.get('choices'):
            for choice in entry['choices']:
                if choice.get('is_roll'):
                    if not choice.get('skill'):
                        issues.append(f"Entry {entry_num}: Roll choice missing skill")
                    if not choice.get('success_destination'):
                        issues.append(f"Entry {entry_num}: Roll choice missing success_destination")
                    if not choice.get('failure_destination'):
                        issues.append(f"Entry {entry_num}: Roll choice missing failure_destination")

        return issues

    def validate_skill_mapping(self, skill_name):
        """Check if skill can be mapped to character skills"""
        if not hasattr(self.char, 'skills'):
            return "Character has no skills dict"

        # Try direct match
        if skill_name in self.char.skills:
            return None

        # Try normalized
        if skill_name.title() in self.char.skills:
            return None

        # Try variations
        variations = {
            'dodge': 'Dodge',
            'archaeology': 'Archaeology',
            'stealth': 'Stealth',
            'fighting': 'Fighting',
            'psychology': 'Psychology',
            'navigation': 'Navigation',
            'listen': 'Listen',
            'locksmith': 'Locksmith',
            'swim': 'Swim',
            'swimming': 'Swim',
        }

        if skill_name.lower() in variations:
            mapped = variations[skill_name.lower()]
            if mapped in self.char.skills:
                return None

        return f"Skill '{skill_name}' cannot be mapped"

    def play_session(self, session_num, strategy='explore'):
        """Play one session with error tracking"""
        session = GameSession(
            session_id=str(uuid.uuid4()),
            character=self.char,
            current_entry=1
        )

        visited = []
        visited_counts = defaultdict(int)
        entry_texts = {}
        rolls_executed = []
        current = 1
        steps = 0
        max_steps = 500

        while steps < max_steps:
            steps += 1

            entry = self.engine.get_entry(current)
            if not entry:
                self.logic_issues.append({
                    'session': session_num,
                    'step': steps,
                    'issue': f"Entry {current} not found (referenced from path)"
                })
                break

            visited.append(current)
            visited_counts[current] += 1
            entry_texts[current] = entry['text'][:100]

            # Validate entry structure
            entry_errors = self.validate_entry(current, entry)
            for err in entry_errors:
                self.parsing_issues.append({
                    'session': session_num,
                    'entry': current,
                    'issue': err
                })

            # Check for THE END
            if "THE END" in entry['text']:
                self.outcomes['ENDING'] += 1
                self.all_paths.append({
                    'session': session_num,
                    'path': visited[:],
                    'outcome': 'ENDING',
                    'steps': steps
                })
                return {
                    'outcome': 'ENDING',
                    'visited': visited,
                    'rolls': rolls_executed,
                    'errors': entry_errors
                }

            # Check for dead end
            if not entry.get('choices'):
                self.outcomes['DEAD_END'] += 1
                self.logic_issues.append({
                    'session': session_num,
                    'step': steps,
                    'entry': current,
                    'issue': 'Dead end - no choices available'
                })
                self.all_paths.append({
                    'session': session_num,
                    'path': visited[:],
                    'outcome': 'DEAD_END',
                    'steps': steps,
                    'at_entry': current
                })
                return {
                    'outcome': 'DEAD_END',
                    'visited': visited,
                    'rolls': rolls_executed,
                    'errors': entry_errors
                }

            # Auto-advance check
            if len(entry['choices']) == 1 and entry['choices'][0]['text'] == '':
                next_entry = entry['choices'][0]['destination']
            else:
                # Choose based on strategy
                if strategy == 'explore':
                    # Prefer unvisited
                    unvisited = [
                        c for c in entry['choices']
                        if visited_counts[c['destination']] == 0
                    ]
                    if unvisited:
                        choice = random.choice(unvisited)
                    else:
                        # Prefer exit/leave choices
                        exit_choices = [
                            c for c in entry['choices']
                            if any(w in c.get('text', '').lower()
                                   for w in ['leave', 'exit', 'proceed', 'go'])
                        ]
                        choice = random.choice(exit_choices) if exit_choices else random.choice(entry['choices'])
                else:
                    choice = random.choice(entry['choices'])

                # Validate choice
                if choice.get('is_roll'):
                    # Validate skill mapping
                    skill = choice.get('skill')
                    skill_error = self.validate_skill_mapping(skill)
                    if skill_error:
                        self.skill_issues.append({
                            'session': session_num,
                            'entry': current,
                            'skill': skill,
                            'issue': skill_error
                        })

                    # Simulate roll
                    rolled = random.randint(1, 100)
                    rolls_executed.append({
                        'entry': current,
                        'skill': skill,
                        'rolled': rolled
                    })
                    self.roll_outcomes['executed'] += 1

                    # Use success/failure destination
                    success = rolled <= 50  # Simplified
                    next_entry = choice.get('success_destination' if success else 'failure_destination')
                    if not next_entry:
                        self.dynamic_issues.append({
                            'session': session_num,
                            'entry': current,
                            'issue': f"Roll missing {'success' if success else 'failure'}_destination"
                        })
                        next_entry = choice.get('destination')
                else:
                    next_entry = choice.get('destination')

            # Validate destination exists
            if next_entry and not (1 <= next_entry <= 243):
                self.continuity_issues.append({
                    'session': session_num,
                    'from': current,
                    'to': next_entry,
                    'issue': f"Invalid destination {next_entry}"
                })
                break

            # Check for excessive loops
            if visited_counts[current] > 5:
                self.logic_issues.append({
                    'session': session_num,
                    'entry': current,
                    'issue': f'Entry visited {visited_counts[current]} times (stuck loop?)'
                })
                self.outcomes['LOOP_DETECTED'] += 1
                return {
                    'outcome': 'LOOP_DETECTED',
                    'visited': visited,
                    'rolls': rolls_executed,
                    'errors': entry_errors
                }

            current = next_entry

        # Timeout
        self.outcomes['TIMEOUT'] += 1
        self.all_paths.append({
            'session': session_num,
            'path': visited[:],
            'outcome': 'TIMEOUT',
            'steps': steps
        })
        return {
            'outcome': 'TIMEOUT',
            'visited': visited,
            'rolls': rolls_executed,
            'errors': entry_errors
        }

def main():
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE GAME ANALYSIS - 500 SESSIONS")
    print("  Validating logic, continuity, parsing, and mechanics")
    print("=" * 80 + "\n")

    analyzer = ComprehensiveGameAnalyzer()
    num_sessions = 500

    print(f"Running {num_sessions} automated playthroughs...\n")

    for session_num in range(1, num_sessions + 1):
        strategy = 'explore' if session_num % 2 == 0 else 'random'
        result = analyzer.play_session(session_num, strategy)

        if session_num % 50 == 0:
            outcomes_so_far = dict(analyzer.outcomes)
            print(f"  {session_num}/{num_sessions} sessions")
            print(f"    Endings: {outcomes_so_far.get('ENDING', 0)}")
            print(f"    Dead Ends: {outcomes_so_far.get('DEAD_END', 0)}")
            print(f"    Loops: {outcomes_so_far.get('LOOP_DETECTED', 0)}")
            print(f"    Timeouts: {outcomes_so_far.get('TIMEOUT', 0)}")
            print(f"    Issues: P:{len(analyzer.parsing_issues)} L:{len(analyzer.logic_issues)} C:{len(analyzer.continuity_issues)} S:{len(analyzer.skill_issues)}")
            print()

    # Analysis report
    print(f"\n{'=' * 80}")
    print("  COMPREHENSIVE ANALYSIS REPORT")
    print(f"{'=' * 80}\n")

    print("OUTCOMES (500 Sessions):")
    for outcome in ['ENDING', 'DEAD_END', 'LOOP_DETECTED', 'TIMEOUT']:
        count = analyzer.outcomes[outcome]
        pct = (count / num_sessions) * 100
        print(f"  {outcome:15s}: {count:3d} sessions ({pct:5.1f}%)")

    print(f"\n{'=' * 80}")
    print("ERROR ANALYSIS")
    print(f"{'=' * 80}\n")

    print(f"PARSING ISSUES: {len(analyzer.parsing_issues)}")
    if analyzer.parsing_issues:
        by_issue = defaultdict(int)
        for issue in analyzer.parsing_issues:
            by_issue[issue['issue']] += 1
        for issue, count in sorted(by_issue.items(), key=lambda x: -x[1])[:10]:
            print(f"  • {issue}: {count} occurrences")

    print(f"\nLOGIC ISSUES: {len(analyzer.logic_issues)}")
    if analyzer.logic_issues:
        by_issue = defaultdict(int)
        for issue in analyzer.logic_issues:
            by_issue[issue['issue']] += 1
        for issue, count in sorted(by_issue.items(), key=lambda x: -x[1])[:10]:
            print(f"  • {issue}: {count} occurrences")

    print(f"\nCONTINUITY ISSUES: {len(analyzer.continuity_issues)}")
    if analyzer.continuity_issues:
        for issue in analyzer.continuity_issues[:5]:
            print(f"  • Session {issue['session']}: {issue['from']} → {issue['to']}")
            print(f"    {issue['issue']}")

    print(f"\nSKILL MAPPING ISSUES: {len(analyzer.skill_issues)}")
    if analyzer.skill_issues:
        by_skill = defaultdict(int)
        for issue in analyzer.skill_issues:
            by_skill[issue['skill']] += 1
        for skill, count in sorted(by_skill.items(), key=lambda x: -x[1])[:10]:
            print(f"  • Skill '{skill}': {count} rolls attempted")

    print(f"\nDYNAMIC ISSUES: {len(analyzer.dynamic_issues)}")
    if analyzer.dynamic_issues:
        by_issue = defaultdict(int)
        for issue in analyzer.dynamic_issues:
            by_issue[issue['issue']] += 1
        for issue, count in sorted(by_issue.items(), key=lambda x: -x[1])[:5]:
            print(f"  • {issue}: {count} occurrences")

    print(f"\n{'=' * 80}")
    print("GAMEPLAY ANALYSIS")
    print(f"{'=' * 80}\n")

    # Unique entries touched
    all_entries_touched = set()
    for path_info in analyzer.all_paths:
        all_entries_touched.update(path_info['path'])

    print(f"Entries covered: {len(all_entries_touched)}/219 ({(len(all_entries_touched)/219)*100:.1f}%)")
    print(f"Rolls executed: {analyzer.roll_outcomes['executed']}")

    # Find most common entry
    entry_frequency = defaultdict(int)
    for path_info in analyzer.all_paths:
        for entry in path_info['path']:
            entry_frequency[entry] += 1

    top_entries = sorted(entry_frequency.items(), key=lambda x: -x[1])[:5]
    print(f"\nMost frequent entries:")
    for entry_num, count in top_entries:
        print(f"  Entry {entry_num}: {count} visits")

    # Success rate
    endings = analyzer.outcomes['ENDING']
    success_rate = (endings / num_sessions) * 100
    print(f"\nSUCCESS RATE: {endings}/{num_sessions} ({success_rate:.1f}%)")

    print(f"\n{'=' * 80}")
    print("STATUS")
    print(f"{'=' * 80}\n")

    total_issues = (len(analyzer.parsing_issues) + len(analyzer.logic_issues) +
                   len(analyzer.continuity_issues) + len(analyzer.skill_issues) +
                   len(analyzer.dynamic_issues))

    if total_issues == 0:
        print("✅ NO ERRORS FOUND - Game is solid!")
    elif total_issues < 20:
        print(f"⚠️  Minor issues found ({total_issues}) - Acceptable")
    elif total_issues < 50:
        print(f"⚠️  Moderate issues found ({total_issues}) - Some attention needed")
    else:
        print(f"❌ Significant issues found ({total_issues}) - Needs work")

    print(f"\n{'=' * 80}\n")

if __name__ == '__main__':
    main()
