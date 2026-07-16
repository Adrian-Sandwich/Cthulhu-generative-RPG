#!/usr/bin/env python3
"""
Playtest analytics — summarize saves, playtest archives, and feedback into a
readable report. Reads from DATA_DIR (default: repo root).

    python3 tools/analyze_playtests.py
"""

import glob
import json
import os
from collections import Counter

DATA = os.environ.get("DATA_DIR", ".")


def _load(pattern):
    for path in glob.glob(os.path.join(DATA, pattern)):
        try:
            with open(path, encoding="utf-8") as f:
                yield path, json.load(f)
        except Exception:
            continue


def _actions(narrative):
    return [l[8:] for l in narrative if l.startswith("Player: ")]


def _rolls(narrative):
    return [l for l in narrative if l.startswith("[ROLL")]


def main():
    saves = list(_load("saves/generative/*.json"))
    playtests = list(_load("playtests/*.json"))

    print("=" * 60)
    print(f"PLAYTEST REPORT  (DATA_DIR={DATA})")
    print("=" * 60)

    # --- sessions (live saves) ---
    print(f"\nSESSIONS: {len(saves)}")
    played = tot_a = tot_r = 0
    turns = []
    sans = []
    for _, d in saves:
        st = d.get("game_state", {})
        inv = st.get("investigator", {})
        acts = _actions(st.get("narrative", []))
        if acts:
            played += 1
            turns.append(st.get("turn", 0))
            sans.append(inv.get("characteristics", {}).get("SAN", 99))
        tot_a += len(acts)
        tot_r += len(_rolls(st.get("narrative", [])))
    print(f"  played (>0 actions): {played} | only opened: {len(saves) - played}")
    print(f"  total actions: {tot_a} | total rolls: {tot_r} | "
          f"dice/action: {tot_r / max(tot_a, 1):.2f}")
    if turns:
        print(f"  turns — max {max(turns)}, avg {sum(turns) / len(turns):.1f}")
        print(f"  lowest SAN reached: {min(sans)}")

    # --- endings (from archives) ---
    if playtests:
        endings = Counter(d.get("ending") or "unfinished" for _, d in playtests)
        print(f"\nARCHIVED RUNS: {len(playtests)}")
        for k, v in endings.most_common():
            print(f"  {k}: {v}")

    # --- feedback ---
    fb_path = os.path.join(DATA, "feedback", "feedback.jsonl")
    if os.path.exists(fb_path):
        rows = [json.loads(l) for l in open(fb_path, encoding="utf-8") if l.strip()]
        ratings = [r["rating"] for r in rows if r.get("rating")]
        print(f"\nFEEDBACK: {len(rows)} entries")
        if ratings:
            print(f"  avg rating: {sum(ratings) / len(ratings):.1f}/5  "
                  f"({len(ratings)} rated)")
        for r in rows[-15:]:
            stars = "★" * (r.get("rating") or 0)
            print(f"  {stars:5s} [{r.get('investigator') or '?'} t{r.get('turn')}] {r['text'][:80]}")
    else:
        print("\nFEEDBACK: none yet")


if __name__ == "__main__":
    main()
