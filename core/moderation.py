#!/usr/bin/env python3
"""
Lightweight content moderation for a public deployment.

Deliberately CONSERVATIVE: this is a cosmic-horror game, so violence, death,
dread, and gore are expected and must NOT be blocked. The local blocklist
targets only categories that are never acceptable regardless of setting
(sexual content involving minors, real-world hate slurs). It is a floor, not a
substitute for a real moderation API.

For stronger coverage set MODERATION=api and provide an OpenAI-compatible
moderation endpoint (LLM_BASE_URL/.../moderations). That path is documented but
off by default to avoid per-turn latency/cost during playtests.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

# Only truly-prohibited categories. Word-boundaried, case-insensitive. Kept
# small on purpose — over-blocking a horror game is its own failure.
_BLOCK_PATTERNS = [
    # sexual content involving minors — non-negotiable
    r"\bchild\s*(?:porn|sex)\b",
    r"\bcp\b(?=.*\b(?:porn|child)\b)",
    r"\bpedo(?:phil)?\b",
    r"\bminor\b(?=.{0,20}\bsex)",
    r"\bunderage\b(?=.{0,20}\bsex)",
    # real-world hate slurs (representative; extend via MODERATION_EXTRA)
    r"\bn[i1]gger\b",
    r"\bfaggot\b",
    r"\bkike\b",
    r"\bspic\b",
    r"\bchink\b",
]

_extra = os.environ.get("MODERATION_EXTRA", "")
if _extra:
    _BLOCK_PATTERNS += [re.escape(w.strip()) for w in _extra.split(",") if w.strip()]

_BLOCK_RE = re.compile("|".join(_BLOCK_PATTERNS), re.IGNORECASE)

MODE = os.environ.get("MODERATION", "local").lower()  # local | off | api


def is_allowed(text: str) -> bool:
    """True if the text passes moderation. Empty/short text is always allowed."""
    if MODE == "off" or not text:
        return True
    if _BLOCK_RE.search(text):
        logger.warning("moderation blocked content")
        return False
    return True
