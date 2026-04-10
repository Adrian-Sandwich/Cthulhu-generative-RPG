#!/usr/bin/env python3
"""
Extractor especializado para "Alone Against the Dark"
Versión flexible que captura todas las entradas numeradas
sin validación demasiado estricta de contexto
"""

import subprocess
import re
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class RollInfo:
    skill: str
    difficulty: str = "Normal"
    on_success: Optional[int] = None
    on_failure: Optional[int] = None
    raw_text: str = ""

@dataclass
class Entry:
    number: int
    text: str
    choices: List[str]
    trace_numbers: List[int]
    character_name: Optional[str] = None
    is_adventure_entry: bool = True
    entry_type: str = "adventure"
    rolls: List[RollInfo] = None

    def __post_init__(self):
        if self.rolls is None:
            self.rolls = []

    def to_dict(self):
        return {
            'number': self.number,
            'text': self.text,
            'choices': self.choices,
            'trace_numbers': self.trace_numbers,
            'character_name': self.character_name,
            'is_adventure_entry': self.is_adventure_entry,
            'entry_type': self.entry_type,
            'rolls': [asdict(r) for r in self.rolls] if self.rolls else []
        }

class FlexibleExtractor:
    def __init__(self, pdf_path: str, total_entries: int):
        self.pdf_path = pdf_path
        self.total_entries = total_entries
        self.lines = self._extract_raw_text()
        self.entry_line_map = self._find_entry_locations()

    def _extract_raw_text(self) -> List[str]:
        result = subprocess.run(
            ['pdftotext', self.pdf_path, '-'],
            capture_output=True,
            text=True
        )
        return result.stdout.split('\n')

    def _find_entry_locations(self) -> Dict[int, int]:
        """Encuentra TODAS las entradas numeradas sin validación estricta"""
        locations = {}
        
        for i, line in enumerate(self.lines):
            # Patrón: número solo en la línea
            match = re.match(r'^\s*(\d{1,3})\s*$', line)
            if match:
                num = int(match.group(1))
                if 1 <= num <= self.total_entries:
                    # Solo registrar la primera ocurrencia de cada número
                    if num not in locations:
                        locations[num] = i

        return locations

    def _extract_rolls_from_choices(self, choices: List[str]) -> List[RollInfo]:
        rolls = []
        for choice in choices:
            if 'roll' in choice.lower() or 'test' in choice.lower():
                roll_info = self._parse_roll_instruction(choice)
                if roll_info:
                    rolls.append(roll_info)
        return rolls

    def _parse_roll_instruction(self, text: str) -> Optional[RollInfo]:
        pattern = r'Make\s+(?:an?\s+)?(\w+(?:\s+\w+)*?)\s+roll(?:\s+\(([^)]+)\))?:\s*if you succeed,\s*go to (\d+);\s*if you fail,\s*go to (\d+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            skill = match.group(1).strip()
            difficulty_text = match.group(2) if match.group(2) else "Normal"
            on_success = int(match.group(3))
            on_failure = int(match.group(4))
            
            difficulty = "Hard" if "hard" in difficulty_text.lower() else \
                        "Extreme" if "extreme" in difficulty_text.lower() else \
                        "Normal"
            
            return RollInfo(
                skill=skill,
                difficulty=difficulty,
                on_success=on_success,
                on_failure=on_failure,
                raw_text=text
            )
        return None

    def _extract_entry_from_pdf(self, entry_num: int) -> Optional[Entry]:
        if entry_num not in self.entry_line_map:
            return None

        start_idx = self.entry_line_map[entry_num]
        
        # Encontrar siguiente entrada
        end_idx = len(self.lines)
        for next_num in sorted(self.entry_line_map.keys()):
            if self.entry_line_map[next_num] > start_idx:
                end_idx = self.entry_line_map[next_num]
                break

        content_lines = []
        choices = []
        trace_numbers = []
        character_name = None
        in_content = False

        for i in range(start_idx + 1, end_idx):
            line = self.lines[i].rstrip()
            stripped = line.strip()

            # Ignorar headers
            if 'ALONE AGAINST' in line or (stripped and all(c in 'BOKRUG ' for c in stripped)):
                continue

            # Choices
            if stripped.startswith('•'):
                choices.append(stripped)
                continue

            # Trace numbers
            if re.match(r'^\s*\([\d\s,]+\)\s*$', stripped):
                numbers_match = re.findall(r'\d+', stripped)
                trace_numbers = [int(n) for n in numbers_match]
                continue

            # Ignorar vacías al inicio
            if not in_content and not stripped:
                continue

            # Posible nombre
            if not in_content and stripped and len(stripped) < 50 and not any(c in stripped for c in '.!?'):
                if re.match(r'^[A-Z][a-zA-Z\s]+$', stripped):
                    character_name = stripped
                    continue

            # Contenido
            if stripped:
                in_content = True
                content_lines.append(stripped)

        full_text = ' '.join(content_lines)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        # Determinar tipo
        entry_type = "adventure"
        is_adventure = True
        text_lower = full_text.lower()

        if not full_text or len(full_text) < 5:
            entry_type = "empty"
            is_adventure = False
        elif choices or trace_numbers:
            entry_type = "adventure"
            is_adventure = True
        elif any(keyword in text_lower for keyword in
                 ['getting started', 'preparing to start', 'reading this book',
                  'introduction', 'what is call of cthulhu']):
            entry_type = "instruction"
            is_adventure = False
        elif len(full_text) < 20:
            entry_type = "empty"
            is_adventure = False

        rolls = self._extract_rolls_from_choices(choices)

        return Entry(
            number=entry_num,
            text=full_text,
            choices=choices,
            trace_numbers=trace_numbers,
            character_name=character_name,
            is_adventure_entry=is_adventure,
            entry_type=entry_type,
            rolls=rolls
        )

    def extract_all(self) -> List[Entry]:
        entries = []
        for num in sorted(self.entry_line_map.keys()):
            entry = self._extract_entry_from_pdf(num)
            if entry:
                entries.append(entry)
        return entries

if __name__ == '__main__':
    print("🔓 EXTRACTOR FLEXIBLE - Alone Against the Dark")
    print("="*80)

    extractor = FlexibleExtractor(
        '/Users/adrianmedina/src/Cthulhu/toaz.info-call-of-cthulhu-alone-against-the-dark-2017-pr_957240174eca06fce7a47b8884b2fc5f.pdf',
        594
    )
    
    print(f"✓ PDF cargado ({len(extractor.lines)} líneas)")
    print(f"✓ Encontradas {len(extractor.entry_line_map)} entradas numeradas")
    print()

    print("Extrayendo...")
    entries = extractor.extract_all()
    print(f"✓ {len(entries)} entradas extraídas")
    print()

    # Estadísticas
    total_chars = sum(len(e.text) for e in entries)
    avg_chars = total_chars / len(entries) if entries else 0
    print("📊 ESTADÍSTICAS:")
    print(f"   Total: {len(entries)}")
    print(f"   Caracteres: {total_chars:,}")
    print(f"   Promedio: {avg_chars:.0f}")
    
    # Guardar
    with open('entries_dark_flexible.json', 'w') as f:
        json.dump([e.to_dict() for e in entries], f, indent=2)
    print(f"\n✓ Guardado en entries_dark_flexible.json")
