#!/usr/bin/env python3
"""
Adventure configuration loader.

Holds the per-adventure data the engine used to hardcode (story seed, starting
location, locations, NPCs, factions, relationships, location keywords, optional
roll-keyword overrides). A new adventure is a new ``adventures/<name>/config.json``
file — no engine edits required.

Note: this is distinct from the branching-narrative ``adventures/*.json`` entry
files; those describe scripted entries/choices, this describes the live world the
generative DM reasons over.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

ADVENTURES_DIR = Path(__file__).resolve().parent.parent / "adventures"

# Relationship types the entity graph accepts (mirrors EntityGraph.ALLOWED_RELS).
_ALLOWED_RELS = {"WORKS_FOR", "KNOWS", "FEARS", "PROTECTS"}


@dataclass
class AdventureConfig:
    """Validated, in-memory view of an adventure's config.json."""
    name: str
    story_seed: str
    start_location: str
    # DM-facing adventure brief (setting, mystery, threat) injected into the
    # system prompt. Optional: engine falls back to its legacy constant.
    description: str = ""
    # Pre-authored translations of story_seed, keyed by language code. Using a
    # static translation makes non-English starts instant and deterministic
    # (no LLM translation, no re-translation on repeated starts).
    story_seed_i18n: Dict[str, str] = field(default_factory=dict)
    locations: List[Dict] = field(default_factory=list)        # {key, name, description}
    location_keywords: Dict[str, str] = field(default_factory=dict)  # narrative keyword -> location name
    npcs: Dict[str, Dict] = field(default_factory=dict)         # key -> {name, role, knows, ...}
    factions: List[Dict] = field(default_factory=list)          # {key, name, alignment}
    relationships: List[Dict] = field(default_factory=list)     # {from, rel, to}
    # keyword -> [skill, difficulty]; None means "use the engine's default map".
    roll_keywords: Optional[Dict[str, List[str]]] = None
    # finite stakes: {"ammo": int, "time_limit": int (turn doom arrives, 0=off)}
    resources: Dict = field(default_factory=dict)

    @classmethod
    def from_name(cls, name: str) -> "AdventureConfig":
        """Load adventures/<name>/config.json."""
        path = ADVENTURES_DIR / name / "config.json"
        if not path.exists():
            raise FileNotFoundError(f"Adventure config not found: {path}")
        return cls.from_json(path, name=name)

    @classmethod
    def from_json(cls, path, name: Optional[str] = None) -> "AdventureConfig":
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data, name=name or data.get("name") or path.parent.name)

    @classmethod
    def from_dict(cls, data: Dict, name: str) -> "AdventureConfig":
        # Lightweight validation — no external schema dependency.
        if not isinstance(data, dict):
            raise ValueError("adventure config must be a JSON object")
        for req in ("story_seed", "start_location"):
            if not data.get(req):
                raise ValueError(f"adventure config '{name}' missing required field: {req}")

        for rel in data.get("relationships", []) or []:
            rtype = rel.get("rel")
            if rtype not in _ALLOWED_RELS:
                raise ValueError(
                    f"adventure '{name}' relationship has invalid rel {rtype!r}; "
                    f"allowed: {sorted(_ALLOWED_RELS)}"
                )

        return cls(
            name=name,
            story_seed=data["story_seed"],
            start_location=data["start_location"],
            description=data.get("description", ""),
            story_seed_i18n=data.get("story_seed_i18n", {}) or {},
            locations=data.get("locations", []) or [],
            location_keywords=data.get("location_keywords", {}) or {},
            npcs=data.get("npcs", {}) or {},
            factions=data.get("factions", []) or [],
            relationships=data.get("relationships", []) or [],
            roll_keywords=data.get("roll_keywords"),
            resources=data.get("resources", {}) or {},
        )
