#!/usr/bin/env python3
"""
Evaluation checklist for generated example images.
Use this to systematically review and rate image quality.
"""

import json
from pathlib import Path


EVALUATION_CRITERIA = {
    "visual_coherence": {
        "description": "Does the image match the scene description?",
        "weight": 2,
        "notes": "Check if elements (lighthouse, moss, glow) are present"
    },
    "horror_aesthetic": {
        "description": "Does it convey Lovecraftian horror atmosphere?",
        "weight": 2,
        "notes": "Oppressive mood, unnatural colors, wrongness"
    },
    "pixel_art_style": {
        "description": "Is it recognizable pixel art?",
        "weight": 1,
        "notes": "Retro aesthetic, not photorealism"
    },
    "first_person_perspective": {
        "description": "Does it feel like a first-person view?",
        "weight": 2,
        "notes": "Depth cues, composition, camera angle"
    },
    "playability": {
        "description": "Works as game background?",
        "weight": 2,
        "notes": "Readable, not too dark/bright, suitable for UI overlay"
    },
    "color_palette": {
        "description": "Matches intended palette?",
        "weight": 1,
        "notes": "Desaturated stones, moss greens, unnatural glows"
    }
}


def create_evaluation_form():
    """Create empty evaluation form for all scenes."""

    scenes = ["lighthouse_exterior", "lighthouse_interior", "underground_cavern"]
    form = {}

    for scene in scenes:
        form[scene] = {
            "ratings": {key: None for key in EVALUATION_CRITERIA.keys()},
            "overall_score": None,
            "notes": "",
            "verdict": ""  # ACCEPT / REVISE / REJECT
        }

    return form


def calculate_score(ratings: dict) -> tuple[float, str]:
    """Calculate weighted score and verdict."""

    scores = []
    weights = []

    for criterion, rating in ratings.items():
        if rating is not None:
            weight = EVALUATION_CRITERIA[criterion]["weight"]
            scores.append(rating * weight)
            weights.append(weight)

    if not scores:
        return 0.0, "NO_RATING"

    weighted_avg = sum(scores) / sum(weights)

    if weighted_avg >= 4.0:
        verdict = "✓ ACCEPT"
    elif weighted_avg >= 3.0:
        verdict = "! REVISE (acceptable with prompt tweaks)"
    else:
        verdict = "✗ REJECT (needs major changes)"

    return weighted_avg, verdict


def print_evaluation_guide():
    """Print guide for manual evaluation."""

    print("\n" + "=" * 70)
    print("IMAGE EVALUATION GUIDE")
    print("=" * 70)

    print("\nRate each criterion on a scale of 1-5:")
    print("  1 = Not at all")
    print("  2 = Poorly")
    print("  3 = Adequately")
    print("  4 = Well")
    print("  5 = Excellently\n")

    for criterion, details in EVALUATION_CRITERIA.items():
        print(f"\n📊 {criterion.upper().replace('_', ' ')}")
        print(f"   Question: {details['description']}")
        print(f"   Notes: {details['notes']}")
        print(f"   Weight: {details['weight']}x")


def show_results_template():
    """Show template for recording evaluations."""

    print("\n" + "=" * 70)
    print("EVALUATION TEMPLATE")
    print("=" * 70)

    template = {
        "lighthouse_exterior": {
            "ratings": {
                "visual_coherence": "YOUR_RATING_1_5",
                "horror_aesthetic": "YOUR_RATING_1_5",
                "pixel_art_style": "YOUR_RATING_1_5",
                "first_person_perspective": "YOUR_RATING_1_5",
                "playability": "YOUR_RATING_1_5",
                "color_palette": "YOUR_RATING_1_5"
            },
            "notes": "What's good/bad about this image?",
            "verdict": "ACCEPT | REVISE | REJECT"
        }
    }

    print(json.dumps(template, indent=2))

    print("\nOnce you've rated all images, save as:")
    print("  game/evaluations.json")


if __name__ == "__main__":
    print_evaluation_guide()
    show_results_template()

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. Look at images in ./generated/")
    print("2. Rate each one using the criteria above")
    print("3. Record ratings in evaluations.json")
    print("4. Share feedback with adjustments needed")
    print("5. Update prompts and regenerate")
