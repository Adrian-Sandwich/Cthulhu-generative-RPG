#!/usr/bin/env python3
"""
The HTTP contract, pinned against a golden captured before the blueprint split.

Acceptance criterion for that refactor: moving views out of create_app must not
change a single route. Nothing else in this repo depends on Flask endpoint
names — the only url_for calls target the built-in 'static' endpoint — so a
blueprint prefix is allowed, but the rule, its methods and the view's own name
are not.

To re-capture after a deliberate route change:
    python3 tests/test_url_map.py --capture
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GOLDEN = Path(__file__).with_name("url_map.golden.json")


def _live_rules():
    import app as app_module
    app_obj = app_module.create_app({"DATA_DIR": tempfile.mkdtemp()})
    rules = [
        {"rule": r.rule,
         "endpoint": r.endpoint,
         "methods": sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"})}
        for r in app_obj.url_map.iter_rules() if r.endpoint != "static"
    ]
    rules.sort(key=lambda d: (d["rule"], d["endpoint"]))
    return rules


def _contract(rules):
    """(rule, methods, view name) — the blueprint prefix is allowed to appear."""
    return sorted(
        (r["rule"], tuple(r["methods"]), r["endpoint"].rsplit(".", 1)[-1])
        for r in rules
    )


def test_url_map_matches_the_golden():
    golden = json.loads(GOLDEN.read_text())
    live = _live_rules()

    want, got = _contract(golden), _contract(live)
    missing = [r for r in want if r not in got]
    added = [r for r in got if r not in want]
    assert not missing, f"routes lost: {missing}"
    assert not added, f"routes added without updating the golden: {added}"


def test_every_route_is_reachable():
    """A rule in the map with no view is a route that 500s on first use."""
    import app as app_module
    app_obj = app_module.create_app({"DATA_DIR": tempfile.mkdtemp()})
    for rule in app_obj.url_map.iter_rules():
        assert rule.endpoint in app_obj.view_functions, rule.endpoint


if __name__ == "__main__":
    if "--capture" in sys.argv:
        GOLDEN.write_text(json.dumps(_live_rules(), indent=2) + "\n")
        print(f"captured {len(_live_rules())} rules to {GOLDEN}")
    else:
        print("run with --capture to re-record the golden")
