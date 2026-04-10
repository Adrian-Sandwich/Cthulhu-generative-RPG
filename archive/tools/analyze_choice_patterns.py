#!/usr/bin/env python3
"""
Analyze choice pattern types in the adventure
Categorize instruction types instead of treating as infinite
"""

import json
import re
from collections import defaultdict

def analyze_choice_patterns():
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'r') as f:
        data = json.load(f)

    # Categorize choices by type
    choice_types = defaultdict(int)
    pattern_examples = defaultdict(list)

    for entry in data['entries']:
        for choice in entry.get('choices', []):
            text = choice.get('text', '').lower().strip()

            # Categorize by pattern
            if not text:
                choice_type = 'AUTO_ADVANCE'
            elif any(kw in text for kw in ['make a ', 'make an ', 'roll']):
                choice_type = 'SKILL_ROLL'
            elif any(kw in text for kw in ['if you ', 'if the ']):
                choice_type = 'CONDITIONAL'
            elif any(kw in text for kw in ['attempt', 'try', 'go', 'head', 'walk', 'move']):
                choice_type = 'ACTION'
            elif any(kw in text for kw in ['ask', 'talk', 'speak', 'inquire']):
                choice_type = 'DIALOGUE'
            elif any(kw in text for kw in ['examine', 'search', 'look', 'investigate']):
                choice_type = 'INVESTIGATION'
            elif any(kw in text for kw in ['leave', 'exit', 'depart', 'return', 'flee']):
                choice_type = 'MOVEMENT'
            else:
                choice_type = 'OTHER'

            choice_types[choice_type] += 1

            if len(pattern_examples[choice_type]) < 3:
                pattern_examples[choice_type].append({
                    'entry': entry['number'],
                    'text': choice.get('text', '')[:60]
                })

    # Print analysis
    print("\n" + "=" * 80)
    print("  CHOICE PATTERN ANALYSIS")
    print("=" * 80 + "\n")

    print("CHOICE TYPE DISTRIBUTION:\n")
    total = sum(choice_types.values())
    for choice_type in sorted(choice_types.keys(), key=lambda x: -choice_types[x]):
        count = choice_types[choice_type]
        pct = (count / total) * 100
        print(f"  {choice_type:20s}: {count:3d} choices ({pct:5.1f}%)")

    print(f"\n{'=' * 80}")
    print("PATTERN EXAMPLES")
    print(f"{'=' * 80}\n")

    for choice_type in sorted(choice_types.keys(), key=lambda x: -choice_types[x])[:10]:
        print(f"{choice_type}:")
        for example in pattern_examples[choice_type]:
            print(f"  Entry {example['entry']:3d}: {example['text']}")
        print()

    # Analyze traces (the list after bullet points)
    print(f"{'=' * 80}")
    print("TRACE ANALYSIS (Cross-references)")
    print(f"{'=' * 80}\n")

    trace_frequency = defaultdict(int)
    total_traces = 0

    for entry in data['entries']:
        traces = entry.get('traces', [])
        total_traces += len(traces)
        for trace in traces:
            trace_frequency[trace] += 1

    print(f"Total cross-references in traces: {total_traces}")
    print(f"Most referenced entries (from trace lists):\n")

    for entry_num, count in sorted(trace_frequency.items(), key=lambda x: -x[1])[:15]:
        print(f"  Entry {entry_num:3d}: {count:2d} cross-references")

    print(f"\n{'=' * 80}")
    print("INSIGHTS")
    print(f"{'=' * 80}\n")

    print("CHOICE TYPES BREAKDOWN:")
    print(f"  • ACTION choices (go, move, etc): {choice_types['ACTION']}")
    print(f"  • SKILL_ROLL choices: {choice_types['SKILL_ROLL']}")
    print(f"  • CONDITIONAL choices (if/then): {choice_types['CONDITIONAL']}")
    print(f"  • DIALOGUE choices (ask/talk): {choice_types['DIALOGUE']}")
    print(f"  • INVESTIGATION choices (examine): {choice_types['INVESTIGATION']}")
    print(f"  • MOVEMENT choices (leave/exit): {choice_types['MOVEMENT']}")
    print(f"  • AUTO_ADVANCE (empty text): {choice_types['AUTO_ADVANCE']}")

    print(f"\nKEY INSIGHT:")
    print(f"  Choice patterns are categorizable by instruction TYPE.")
    print(f"  Instead of treating bullet points as infinite,")
    print(f"  they follow these {len(choice_types)} distinct patterns.")
    print(f"  Each pattern has consistent semantics and handling.")

    print(f"\n{'=' * 80}\n")

if __name__ == '__main__':
    analyze_choice_patterns()
