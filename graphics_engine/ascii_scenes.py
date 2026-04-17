#!/usr/bin/env python3
"""
ASCII Art Scene Generator for Lovecraftian Adventure
Dynamic atmospheric scenes for locations based on game state
"""

from enum import Enum
from typing import Dict

class WeatherCondition(Enum):
    CLEAR = "clear"
    STORM = "storm"
    FOG = "fog"
    NIGHT = "night"


class LighthouseScenes:
    """Lighthouse location with multiple atmospheric variations"""

    @staticmethod
    def exterior_stormy() -> str:
        """Lighthouse exterior during violent storm"""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║                  THE LIGHTHOUSE - STORMY NIGHT                            ║
╚═══════════════════════════════════════════════════════════════════════════╝

                                                                    . . * .
                                                                  .  * . *
                                                                . * . . * .
                              ⚡                           . * . * . . * .
                                                        . . * . * . * . .
                                                      . * . . * . . * . *
                                                    * . * . . * . * . . *
                                                  . . * . * . . * . * . .
                            ╱─────────╲
                           ╱           ╲              ⚡
                          │      ◯      │          . . * . * .
                          │  ◯ ◯   ◯ ◯  │        . * . . * . * .
                          │      ◯      │      . . * . * . . * .
                           ╲           ╱     . * . . * . * . . *
                            ╲─────────╱    . . * . * . . * . * .
                             │   │   │   . * . . * . . * . * . .
                             │   │   │  * . * . . * . * . . * .
                             │ ◯ │ ◯ │ . . * . * . . * . * . . *
                             │   │   │. * . . * . * . . * . * .
                             │   │   │ . . * . * . . * . * . .
                             │   │   │  ⚡
                             │   │   │
                            ╱     ▔     ╲
                           ╱       ▔       ╲
                          │     ▔ ▔ ▔     │
                           ╲   ▔ ▔ ▔ ▔   ╱
                            ╲___________╱

    ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
    ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~
    ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~

    The lighthouse beam cuts through the storm, revealing nothing but
    churning darkness and rain-swept coastal rocks below. Thunder rumbles
    across the water as another flash of lightning illuminates the tower—
    ancient, weathered, and somehow watching...
"""

    @staticmethod
    def exterior_night_clear() -> str:
        """Lighthouse on a clear, moonlit night"""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║                  THE LIGHTHOUSE - CLEAR NIGHT                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

                                    ☾

                                           ★
                            ╱─────────╲
                           ╱           ╲              ★
                          │      ◯      │
                          │  ◯ ◯   ◯ ◯  │      ★
                          │      ◯      │
                           ╲           ╱     ★
                            ╲─────────╱
                             │   │   │
                             │   │   │
                             │ ◯ │ ◯ │ ★
                             │   │   │
                             │   │   │
                             │   │   │
                             │   │   │
                            ╱     ▔     ╲
                           ╱       ▔       ╲
                          │     ▔ ▔ ▔     │
                           ╲   ▔ ▔ ▔ ▔   ╱
                            ╲___________╱

    ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~
    ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

    The beacon's light sweeps across black water. Stars pierce the darkness
    above, but they seem too distant, too cold. The stone beneath the
    lighthouse has weathered countless storms. How many shipwrecks lie
    in these waters? How many have seen what the lighthouse truly guards?
"""

    @staticmethod
    def exterior_fog() -> str:
        """Lighthouse shrouded in thick fog"""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║                  THE LIGHTHOUSE - FOG                                     ║
╚═══════════════════════════════════════════════════════════════════════════╝

    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
    ░                                                                      ░
    ░                       ~  ~  ~  ~                                    ░
    ░                     ~           ~                                   ░
    ░                                                                      ░
    ░                           ╱─────────╲                               ░
    ░                          ╱   ~ ~ ~   ╲                              ░
    ░                         │   ◯ ~ ◯    │                             ░
    ░                         │  ◯ ~ ~ ◯   │                             ░
    ░                         │      ◯     │    ~  ~                      ░
    ░                          ╲   ~ ~ ~  ╱   ~                           ░
    ░                           ╲─────────╱  ~                            ░
    ░                            │ ~ │ ~ │~                              ░
    ░                            │   │   │                                ░
    ░                            │   │   │                                ░
    ░                            │   │   │                                ░
    ░                            │   │   │                                ░
    ░                           ╱ ~ ▔ ~ ▔ ╲                              ░
    ░                          ╱   ▔▔▔▔▔    ╲                             ░
    ░                         │    ▔▔▔▔▔    │                            ░
    ░                          ╲  ▔ ▔ ▔ ▔  ╱                             ░
    ░                           ╲___________╱                             ░
    ░                                                                      ░
    ░  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~      ░
    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

    A dense fog obscures everything. The lighthouse beam penetrates only
    a few feet before being swallowed by whiteness. You can't see the water,
    can't see the rocks below. Only the sound of the fog horn—a rhythmic,
    mournful call that seems to answer something far out in the mist.
"""

    @staticmethod
    def exterior_dawn() -> str:
        """Lighthouse at dawn with pale light"""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║                  THE LIGHTHOUSE - DAWN                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

                                 ◑


                            ╱─────────╲
                           ╱           ╲
                          │      ◯      │
                          │  ◯ ◯   ◯ ◯  │
                          │      ◯      │
                           ╲           ╱
                            ╲─────────╱
                             │   │   │
                             │   │   │
                             │ ◯ │ ◯ │
                             │   │   │
                             │   │   │
                             │   │   │
                             │   │   │
                            ╱     ▔     ╲
                           ╱       ▔       ╲
                          │     ▔ ▔ ▔     │
                           ╲   ▔ ▔ ▔ ▔   ╱
                            ╲___________╱

    ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
    ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~

    Grey light seeps across the water. The storm has passed. The lighthouse
    still stands, as it always has—will always stand. You notice something
    carved into the base of the tower. Old markings. Too old.
"""

    @staticmethod
    def interior_stairs() -> str:
        """Interior - spiral staircase"""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║              LIGHTHOUSE INTERIOR - SPIRAL STAIRCASE                        ║
╚═══════════════════════════════════════════════════════════════════════════╝


                                    ╔════╗
                                   ╱      ╲
                                  │   ◯◯   │    🕯️  Candlelight flickers
                                   ╲      ╱
                                    ╚════╝
                                      │
                                 ╔═══════╗
                                ╱         ╲
                               │   ◯◯◯◯   │
                              ╱   ╱   ╲   ╲
                             │    │     │   │
                              ╲   ╲   ╱   ╱
                               ╲         ╱
                                ╚═══════╝
                                    │
                               ╔═════════╗
                              ╱           ╲
                             │   ◯◯◯◯◯◯   │
                            ╱   ╱     ╲   ╲
                           │    │       │   │
                          ╱     │       │   ╲
                         │      ╲     ╱      │
                          ╲      ╲   ╱      ╱
                           ╲           ╱
                            ╚═════════╝
                                ╱ ╲
                               │   │
                              ╱     ╲

    The stairs spiral downward endlessly. Each step echoes with your weight.
    Carved into the walls—symbols you don't recognize. The air grows colder
    as you descend. And that sound again. Like breathing. Like something
    enormous waiting in the dark below, patient and aware.
"""

    @staticmethod
    def interior_library() -> str:
        """Interior - keeper's library with forbidden books"""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║              LIGHTHOUSE INTERIOR - KEEPER'S LIBRARY                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

    ╔════════╗  ╔════════╗  ╔════════╗
    ║ ═ ═ ═ ║  ║ ═ ═ ═ ║  ║ ═ ═ ═ ║
    ║ ▓ ▓ ▓ ║  ║ ▓ ▓ ▓ ║  ║ ▓ ▓ ▓ ║
    ║ ═ ═ ═ ║  ║ ═ ═ ═ ║  ║ ═ ═ ═ ║
    ║ ░ ░ ░ ║  ║ ░ ░ ░ ║  ║ ░ ░ ░ ║
    ║ ═ ═ ═ ║  ║ ═ ═ ═ ║  ║ ═ ═ ═ ║
    ║ ▓ ▓ ▓ ║  ║ ▓ ▓ ▓ ║  ║ ▓ ▓ ▓ ║
    ╚════════╝  ╚════════╝  ╚════════╝

    ╔════════╗  ╔════════╗  ╔════════╗
    ║ ═ ═ ═ ║  ║ ═ ═ ═ ║  ║ ═ ═ ═ ║
    ║ ░ ░ ░ ║  ║ ▓ ▓ ▓ ║  ║ ▓ ▓ ▓ ║
    ║ ═ ═ ═ ║  ║ ═ ═ ═ ║  ║ ═ ═ ═ ║
    ║ ▓ ▓ ▓ ║  ║ ░ ░ ░ ║  ║ ░ ░ ░ ║
    ║ ═ ═ ═ ║  ║ ═ ═ ═ ║  ║ ═ ═ ═ ║
    ║ ░ ░ ░ ║  ║ ▓ ▓ ▓ ║  ║ ▓ ▓ ▓ ║
    ╚════════╝  ╚════════╝  ╚════════╝

            ╔════╗
            ║ ▓▓ ║  A massive tome bound in what looks
            ║ ▓▓ ║  like... is that leather? The spine
            ║ ▓▓ ║  is marked with symbols that hurt to
            ║▓▓ ▓║  look at directly. You pick it up.
            ║▓▓▓▓║  The pages are warm.
            ╚════╝

    Countless books line the walls. Some are recent—leather bindings,
    clear titles. Others are ancient, pages yellowed to brittle parchment.
    The keeper was obsessive. Years of observations. Year after year of
    recording what came from the sea. What watched from below.

    One shelf is locked behind iron grating. The books behind it are
    written in no language you recognize.
"""


class AdvancedLighthouseScenes:
    """Extended scenes with interactive elements"""

    @staticmethod
    def beacon_room() -> str:
        """The lighthouse beacon chamber"""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║                      THE BEACON CHAMBER                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

                              ✦ ✦ ✦
                            ✦   ◯   ✦          Blinding light rotates
                          ✦   ◯ ◯ ◯   ✦        slowly overhead,
                           ✦   ◯ ◯   ✦         sweeping across the dark
                             ✦ ✦ ✦            waters in an endless vigil.
                              │ │ │
                              │ │ │
                    ╔═════════╗ │ │ ╔═════════╗
                    ║ ═════ ║ │ │ ║ ═════ ║
                    ║ ═════ ║─┘ └─║ ═════ ║
                    ║ ═════ ║     ║ ═════ ║
                    ║ ═════ ║     ║ ═════ ║
                    ��═════════════════════╝
                    ║                     ║
                    ║                     ║
                    ║                     ║
                    ║                     ║
                    ║                     ║
                    ║                     ║
                    ╚═════════════════════╝

    The massive lamp is ancient—older than the tower around it, you'd
    swear. The light is too bright, too perfect, geometrically precise
    in ways light shouldn't be. When you look directly at it, you see
    something else beneath the glow. Something that isn't the lamp.

    Something looking back.
"""

    @staticmethod
    def keeper_chamber() -> str:
        """The keeper's private chamber"""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║                      THE KEEPER'S CHAMBER                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

            ╔═════════════════════════════════╗
            ║ ┌─────────────────────────────┐ ║
            ║ │         :::::::::::::::     │ ║
            ║ │         : sleeping :  :     │ ║     A simple bed.
            ║ │         :   area   :  :     │ ║     A desk with journals.
            ║ │         :::::::::::::::     │ ║     Empty bottles.
            ║ │                             │ ║
            ║ │  ╔════╗   ╔════╗   ╔════╗  │ ║
            ║ │  ║ ═══ ║   ║ ═══ ║   ║ ═══ ║  │ ║
            ║ │  ║ ▓▓▓ ║   ║ ░░░ ║   ║ ▓▓▓ ║  │ ║
            ║ │  ╚════╝   ╚════╝   ╚════╝  │ ║     The last entry is
            ║ │                             │ ║     dated three weeks ago:
            ║ │     ╔═════════════╗         │ ║
            ║ │     ║ ≈≈≈ DESK ≈≈≈║         │ ║     "I cannot look at it
            ║ │     ║             ║         │ ║      anymore. Every night
            ║ │     ║ ~journals~  ║         │ ║      it rises closer.
            ║ │     ║             ║         │ ║
            ║ │     ╚═════════════╝         │ ║      God forgive me."
            ║ └─────────────────────────────┘ ║
            ╚═════════════════════════════════╝

    The keeper is gone. The last journal entry trails off in an illegible
    scrawl. The window faces the sea. You notice scratches on the frame—
    as if someone had tried to nail it shut from the inside.
"""


# Scene registry for easy access
LIGHTHOUSE_SCENES = {
    "exterior_storm": LighthouseScenes.exterior_stormy,
    "exterior_clear": LighthouseScenes.exterior_night_clear,
    "exterior_fog": LighthouseScenes.exterior_fog,
    "exterior_dawn": LighthouseScenes.exterior_dawn,
    "interior_stairs": LighthouseScenes.interior_stairs,
    "interior_library": LighthouseScenes.interior_library,
    "beacon_room": AdvancedLighthouseScenes.beacon_room,
    "keeper_chamber": AdvancedLighthouseScenes.keeper_chamber,
}


def get_scene(scene_key: str) -> str:
    """Get a scene by key"""
    if scene_key in LIGHTHOUSE_SCENES:
        return LIGHTHOUSE_SCENES[scene_key]()
    return "Scene not found."


def list_scenes() -> Dict[str, str]:
    """List all available scenes"""
    return {key: value.__doc__ or key for key, value in LIGHTHOUSE_SCENES.items()}


if __name__ == "__main__":
    # Demo: show all lighthouse scenes
    print("\n" + "="*80)
    print("LIGHTHOUSE ASCII SCENES DEMO")
    print("="*80)

    for scene_key in LIGHTHOUSE_SCENES:
        print(f"\n{'='*80}")
        print(f"Scene: {scene_key}")
        print(f"{'='*80}")
        print(get_scene(scene_key))
        input("\nPress ENTER for next scene...")
