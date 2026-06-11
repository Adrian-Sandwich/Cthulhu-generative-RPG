#!/usr/bin/env python3
"""
Art Director: converts SceneSpec to visual prompts for image generation.
Enforces visual consistency via style bible.
"""

import json
from pathlib import Path
from game.scene_spec import SceneSpec
from typing import Tuple


def load_style_bible(path: str = None) -> dict:
    """Load style bible rules."""
    if path is None:
        # Find relative to this file
        path = Path(__file__).parent / "style_bible.json"
    else:
        path = Path(path)

    with open(path) as f:
        return json.load(f)


def spec_to_prompt(spec: SceneSpec, style_bible: dict) -> Tuple[str, str]:
    """
    Convert SceneSpec to (positive_prompt, negative_prompt) for Stable Diffusion.
    Optimized for SHORT prompts (< 100 chars) to avoid CLIP truncation.
    Returns: (prompt, negative_prompt)
    """

    # Location descriptions - CONCISE + PIXEL ART FOCUSED
    location_desc = {
        "decaying_chamber": "Decaying stone chamber. Cracked walls, moss. Pixel art.",
        "forest_entrance": "Dark forest entrance. Gnarled trees, shadows. Retro pixel art.",
        "altar_room": "Ritual chamber. Central altar, carved symbols. Pixel art horror.",
        "lighthouse_exterior": "Lighthouse on rocky coast. Pixel art, retro style. First-person.",
        "lighthouse_interior": "Lighthouse interior. Spiral stairs, railings. Pixel art.",
        "underground_cavern": "Underground cavern. Crystals, pools. Dark pixel art.",
        "ritual_chamber": "Ritual chamber. Ancient symbols, oppressive. Pixel art.",
        "keeper_quarters": "Keeper's quarters. Sparse, logbooks. Dark pixel art.",
        "spiral_staircase": "Spiral staircase. Ascending darkness. Retro pixel art."
    }

    # Mood modifiers
    mood_desc = {
        "oppressive_horror": "oppressive, suffocating, sense of impending doom",
        "creeping_dread": "unsettling, unnatural, dread-filled, subtle wrongness",
        "otherworldly": "alien, incomprehensible, geometrically wrong",
        "sanity_breaking": "mind-bending, reality-warping, perception-breaking",
        "eerie_quiet": "silent, desolate, hauntingly still, abandoned",
        "alien_wrongness": "cosmic wrongness, non-euclidean, inhuman scale",
        "cosmic_scale": "vast incomprehensible scale, insignificance of humans"
    }

    # Contamination visual additions
    contamination_desc = ""
    if spec.contamination >= 75:
        contamination_desc = "Reality-breaking geometry, impossible angles, non-euclidean structure, "
    elif spec.contamination >= 50:
        contamination_desc = "Unnatural symbols covering surfaces, bioluminescent growths, warped perspective, "
    elif spec.contamination >= 25:
        contamination_desc = "Faint unnatural markings, subtle color shifts, geometric wrongness, "

    # Danger visual additions
    danger_desc = ""
    if spec.danger_level >= 4:
        danger_desc = "Sense of immediate threat, hostile presence implied, "
    elif spec.danger_level >= 3:
        danger_desc = "Threatening atmosphere, supernatural signs visible, "
    elif spec.danger_level >= 2:
        danger_desc = "Subtle wrongness, increasing danger implied, "

    # Build SHORT prompt (< 100 chars to avoid CLIP truncation)
    location = location_desc.get(spec.location_type, spec.location_type)
    mood = mood_desc.get(spec.mood, spec.mood)

    # Simplified: only most important elements
    prompt = f"{location} {mood}. First-person. No people."

    # Add key objects only if space
    if spec.objects and len(prompt) < 80:
        key_objects = [obj.type for obj in spec.objects[:2]]  # Only first 2
        if key_objects:
            prompt += f" {', '.join(key_objects)}."

    # Build negative prompt
    forbidden = style_bible["forbidden"] + spec.forbidden
    negative_prompt = ", ".join(forbidden)

    return prompt, negative_prompt


def prompt_with_context(
    spec: SceneSpec,
    narrative_excerpt: str,
    style_bible: dict
) -> Tuple[str, str]:
    """
    Generate prompt informed by recent narrative text.
    Allows narrative to influence visual direction.
    """

    prompt, negative = spec_to_prompt(spec, style_bible)

    # Parse narrative for additional clues
    # (In production, could use LLM to extract visual keywords from narrative)
    narrative_lower = narrative_excerpt.lower()

    # Simple heuristics
    if "rain" in narrative_lower or "wet" in narrative_lower:
        prompt += " Rain-soaked surfaces. Water dripping. "
    if "dead" in narrative_lower or "corpse" in narrative_lower or "body" in narrative_lower:
        prompt += " Signs of death and decay. "
    if "glow" in narrative_lower or "light" in narrative_lower:
        prompt += " Unnatural luminescence highlighting the scene. "
    if "sound" in narrative_lower and "silent" in narrative_lower:
        prompt += " Deafening silence visually implied. "

    return prompt, negative


if __name__ == "__main__":
    # Test
    from scene_spec import EXAMPLE_SCENES

    style_bible = load_style_bible()

    for key, spec in EXAMPLE_SCENES.items():
        prompt, negative = spec_to_prompt(spec, style_bible)
        print(f"\n=== {key} ===")
        print(f"PROMPT:\n{prompt}\n")
        print(f"NEGATIVE:\n{negative}\n")
