#!/usr/bin/env python3
"""
Parser de instrucciones de Rolls/Tests en aventuras solitarias.

Extrae y estructura las instrucciones de tiradas de dados del formato:
  "Make a SKILL roll: if you succeed, go to X; if you fail, go to Y."

Genera:
  {
    "type": "roll",
    "skill": "Fast Talk",
    "difficulty": "Normal",
    "on_success": 46,
    "on_failure": 101,
    "extra_options": []
  }
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum


class Difficulty(Enum):
    NORMAL = "Normal"
    HARD = "Hard"
    EXTREME = "Extreme"


@dataclass
class RollInstruction:
    """Instrucción de tirada de dado"""
    skill: str
    difficulty: str
    on_success: Optional[int]
    on_failure: Optional[int]
    extra_text: str = ""

    def __repr__(self):
        return f"Roll({self.skill} [{self.difficulty}] → S:{self.on_success}/F:{self.on_failure})"


class RollParser:
    """Parser de instrucciones de rolls"""

    # Patrones para diferentes estilos de instrucciones
    PATTERNS = [
        # Patrón 1: "Make a SKILL roll: if you succeed, go to X; if you fail, go to Y."
        r'Make\s+(?:an?\s+)?(\w+(?:\s+\w+)*?)\s+roll(?:\s+\(([^)]+)\))?:\s*if you succeed,\s*go to (\d+);\s*if you fail,\s*go to (\d+)',

        # Patrón 2: "Make a SKILL roll (DIFFICULTY) - success: X, failure: Y"
        r'Make\s+(?:an?\s+)?(\w+(?:\s+\w+)*?)\s+roll\s+\(([^)]+)\)\s*[:-]\s*(?:success|succeed).*?(\d+).*?(?:fail|failure).*?(\d+)',

        # Patrón 3: "Test SKILL: success X, failure Y"
        r'Test\s+(?:an?\s+)?(\w+(?:\s+\w+)*?)[:\s]+.*?(?:success|succeed).*?(\d+).*?(?:fail|failure).*?(\d+)',

        # Patrón 4: "Make a SKILL roll" (sin destinos, puede estar incompleto)
        r'Make\s+(?:an?\s+)?(\w+(?:\s+\w+)*?)\s+roll(?:\s+\(([^)]+)\))?',
    ]

    DIFFICULTY_KEYWORDS = {
        'hard': Difficulty.HARD,
        'extreme': Difficulty.EXTREME,
        'normal': Difficulty.NORMAL,
    }

    SKILLS = [
        'Accounting', 'Anthropology', 'Appraise', 'Archeology',
        'Art', 'Assess Honesty', 'Charm', 'Climb', 'Craft',
        'Credit Rating', 'Cthulhu Mythos', 'Debate', 'Disguise',
        'Dodge', 'Electrical Repair', 'Elusive', 'Fighting',
        'Firearms', 'First Aid', 'Flattery', 'Forgery',
        'Jump', 'Knife', 'Language', 'Law', 'Library Use',
        'Listen', 'Locksmith', 'Mechanical Repair', 'Medicine',
        'Natural World', 'Navigate', 'Occult', 'Persuade',
        'Photography', 'Physics', 'Pilot', 'Pistol', 'Psychology',
        'Psychoanalysis', 'Ride', 'Rifle', 'Shotgun', 'Sleight of Hand',
        'Spot Hidden', 'Stealth', 'Surgery', 'Survival', 'Swim',
        'Taunt', 'Throw', 'Track', 'Unnatural', 'Whip',
        'Brawl', 'Melee Weapons',
    ]

    @staticmethod
    def extract_difficulty(text: str) -> str:
        """Extrae dificultad del texto"""
        text_lower = text.lower()
        for keyword, difficulty in RollParser.DIFFICULTY_KEYWORDS.items():
            if keyword in text_lower:
                return difficulty.value
        return "Normal"

    @staticmethod
    def extract_destinations(text: str) -> tuple:
        """Extrae números de destino (go to X)"""
        # Buscar "go to NN"
        matches = re.findall(r'go to (\d+)', text, re.IGNORECASE)
        if len(matches) >= 2:
            return int(matches[0]), int(matches[1])  # success, failure
        elif len(matches) == 1:
            return int(matches[0]), None
        return None, None

    @classmethod
    def parse(cls, text: str) -> Optional[RollInstruction]:
        """
        Intenta parsear una instrucción de roll de un texto.
        Retorna RollInstruction o None si no es un roll válido.
        """
        if not text or 'roll' not in text.lower():
            return None

        # Intenta con cada patrón
        for pattern in cls.PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()

                if len(groups) >= 4:
                    # Patrón con destinos explícitos
                    skill = groups[0].strip()
                    difficulty_text = groups[1] if groups[1] else ""
                    on_success = int(groups[2]) if groups[2] else None
                    on_failure = int(groups[3]) if groups[3] else None

                elif len(groups) == 2:
                    # Solo skill y dificultad, sin destinos
                    skill = groups[0].strip()
                    difficulty_text = groups[1] if groups[1] else ""
                    on_success, on_failure = cls.extract_destinations(text)

                else:
                    continue

                # Normalizar nombre de habilidad
                skill = cls._normalize_skill(skill)
                difficulty = cls.extract_difficulty(difficulty_text)

                return RollInstruction(
                    skill=skill,
                    difficulty=difficulty,
                    on_success=on_success,
                    on_failure=on_failure,
                    extra_text=text
                )

        return None

    @classmethod
    def _normalize_skill(cls, skill: str) -> str:
        """Normaliza el nombre de habilidad"""
        skill_clean = skill.strip()

        # Mapeo de variantes a nombre canónico
        skill_map = {
            'fast talk': 'Persuade',
            'brawl': 'Fighting (Brawl)',
            'fighting': 'Fighting',
            'melee': 'Fighting',
            'credit rating': 'Credit Rating',
            'cthulhu mythos': 'Cthulhu Mythos',
            'spot hidden': 'Spot Hidden',
            'listen': 'Listen',
            'psychology': 'Psychology',
            'appraise': 'Appraise',
            'jump': 'Jump',
            'climb': 'Climb',
            'stealth': 'Stealth',
            'dodge': 'Dodge',
            'charm': 'Charm',
        }

        skill_lower = skill_clean.lower()
        for key, normalized in skill_map.items():
            if key in skill_lower:
                return normalized

        return skill_clean


def parse_entry_for_rolls(entry: dict) -> List[RollInstruction]:
    """
    Dado una entrada del JSON, extrae todas las instrucciones de rolls.
    """
    rolls = []

    # Combinar texto y choices
    all_text = entry.get('text', '') + '\n' + '\n'.join(entry.get('choices', []))

    # Buscar cada línea de choice que sea un roll
    for choice in entry.get('choices', []):
        roll = RollParser.parse(choice)
        if roll:
            rolls.append(roll)

    return rolls


if __name__ == '__main__':
    # Pruebas
    test_cases = [
        "Make a Fast Talk roll: if you succeed, go to 46; if you fail, go to 101.",
        "Make a Psychology roll: if you succeed, go to 126; if you fail, go to 144.",
        "Make an Appraise or Credit Rating roll: if you succeed, go to 100; if you fail, go to 14.",
        "To attempt an escape, make a Hard Fighting (Brawl) roll (success go to 77, failure go to 82)",
        "Make a Spot Hidden roll: if you succeed, go to 28; if you fail, go to 50.",
    ]

    print("PRUEBAS DE PARSER DE ROLLS")
    print("="*80)

    for test in test_cases:
        print(f"\nInput: {test[:70]}...")
        roll = RollParser.parse(test)
        if roll:
            print(f"✓ Parseado: {roll}")
        else:
            print(f"✗ No se pudo parsear")
