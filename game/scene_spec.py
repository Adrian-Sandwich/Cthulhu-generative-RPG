#!/usr/bin/env python3
"""
SceneSpec: structured representation of a scene for deterministic image generation.
Bridges narrative description → visual generation.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
import json


@dataclass
class LightingSpec:
    source: str
    color: str
    intensity: str  # pitch_black, dim, low, moderate, unnatural, pulsing


@dataclass
class SceneObject:
    type: str
    position: str
    state: Optional[str] = None


@dataclass
class SceneSpec:
    """Structured scene specification for image generation."""

    location_key: str
    location_type: str
    mood: str
    lighting: LightingSpec
    objects: List[SceneObject] = field(default_factory=list)
    palette: List[str] = field(default_factory=list)
    camera: str = "wide_eye_level"
    danger_level: int = 1
    contamination: int = 0
    forbidden: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "location_key": self.location_key,
            "location_type": self.location_type,
            "mood": self.mood,
            "lighting": asdict(self.lighting),
            "objects": [asdict(obj) for obj in self.objects],
            "palette": self.palette,
            "camera": self.camera,
            "danger_level": self.danger_level,
            "contamination": self.contamination,
            "forbidden": self.forbidden
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> "SceneSpec":
        lighting = LightingSpec(**data["lighting"])
        objects = [SceneObject(**obj) for obj in data.get("objects", [])]

        return cls(
            location_key=data["location_key"],
            location_type=data["location_type"],
            mood=data["mood"],
            lighting=lighting,
            objects=objects,
            palette=data.get("palette", []),
            camera=data.get("camera", "wide_eye_level"),
            danger_level=data.get("danger_level", 1),
            contamination=data.get("contamination", 0),
            forbidden=data.get("forbidden", [])
        )


# Example scenes for testing
EXAMPLE_SCENES = {
    "lighthouse_exterior": SceneSpec(
        location_key="lighthouse_exterior",
        location_type="lighthouse_exterior",
        mood="eerie_quiet",
        lighting=LightingSpec(
            source="distant_moon",
            color="pale_gray_blue",
            intensity="low"
        ),
        objects=[
            SceneObject("lighthouse_tower", "center_background", "weathered_ancient"),
            SceneObject("rocky_shore", "center_foreground", "wet_jagged"),
            SceneObject("fog_bank", "left_background"),
            SceneObject("abandoned_dock", "right_midground", "rotting")
        ],
        palette=["storm_gray", "pale_blue", "dark_rock", "black"],
        camera="wide_eye_level",
        danger_level=1,
        contamination=10
    ),

    "lighthouse_interior": SceneSpec(
        location_key="lighthouse_interior",
        location_type="lighthouse_interior",
        mood="oppressive_horror",
        lighting=LightingSpec(
            source="ceiling_beam",
            color="sickly_amber",
            intensity="moderate"
        ),
        objects=[
            SceneObject("spiral_stairs", "center_midground"),
            SceneObject("iron_railing", "left_midground", "rusty"),
            SceneObject("stone_walls", "background", "cracked_weathered"),
            SceneObject("hanging_chains", "ceiling"),
            SceneObject("floor_grating", "floor", "corroded")
        ],
        palette=["rust_brown", "stone_gray", "amber_dim", "shadow_black"],
        camera="tall_chamber",
        danger_level=2,
        contamination=30
    ),

    "underground_cavern": SceneSpec(
        location_key="underground_cavern",
        location_type="underground_cavern",
        mood="alien_wrongness",
        lighting=LightingSpec(
            source="glowing_crystals_and_pools",
            color="sickly_cyan_green",
            intensity="unnatural"
        ),
        objects=[
            SceneObject("jagged_crystal_formations", "ceiling", "glowing"),
            SceneObject("luminescent_pool", "center_foreground", "still_glowing"),
            SceneObject("bone_white_structures", "right_midground", "arranged"),
            SceneObject("pulsing_fungal_masses", "left_background", "organic"),
            SceneObject("cave_walls", "background", "carved_wrong")
        ],
        palette=["sickly_green", "deep_cyan", "bone_white", "void_black"],
        camera="wide_eye_level",
        danger_level=4,
        contamination=75
    )
}
