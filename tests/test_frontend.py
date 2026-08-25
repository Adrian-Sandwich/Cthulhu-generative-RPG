#!/usr/bin/env python3
"""
Frontend checks, run through pytest so `pytest` stays the single entry point.

The client is five classic scripts with no other automated coverage. Two regressions
in a row (the deleted location resolver, the invalid `request.is_disconnected`)
shipped because a test existed but could not reach the code that mattered, so
these checks assert behavior rather than presence wherever they can.

Node does the actual work — see tests/frontend_checks.mjs.
Run: pytest tests/test_frontend.py -q
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")

# Skipping is a silent pass, which is how coverage quietly disappears. A
# developer without node gets a skip; CI must have it or fail loudly.
_IN_CI = bool(os.environ.get("CI"))

if NODE is None and _IN_CI:
    pytest.fail("node is required for the frontend checks in CI", pytrace=False)

pytestmark = pytest.mark.skipif(
    NODE is None, reason="node not installed — install Node to run the frontend checks"
)


def _run(*args):
    return subprocess.run(
        [NODE, *args], cwd=REPO, capture_output=True, text=True, timeout=60
    )


CLIENT_FILES = [f"static/js/{n}.js" for n in ("state", "audio", "ui", "turn", "dice")]


@pytest.mark.parametrize("script", CLIENT_FILES)
def test_client_script_parses(script):
    """A syntax error in any of them takes the whole client down silently."""
    assert (REPO / script).exists(), f"{script} is referenced but missing"
    res = _run("--check", script)
    assert res.returncode == 0, res.stderr


def test_index_loads_every_client_script_in_order():
    """The browser sees these as one program; load order is the contract."""
    html = (REPO / "templates" / "index.html").read_text()
    positions = [html.index(f"js/{n}.js") for n in
                 ("state", "audio", "ui", "turn", "dice")]
    assert positions == sorted(positions), "scripts are out of dependency order"


def test_frontend_behavior_checks():
    """Roll-request interception, guard wiring, and onboarding affordances."""
    res = _run("tests/frontend_checks.mjs")
    sys.stdout.write(res.stdout)
    assert res.returncode == 0, res.stdout + res.stderr
