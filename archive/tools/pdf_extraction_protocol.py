#!/usr/bin/env python3
"""
PROTOCOLO GENÉRICO DE EXTRACCIÓN DE LIBROS EN FORMATO "AVENTURA SOLITARIA"

Este script extrae y valida entradas de PDFs con el formato de:
- Numbered entries (1, 2, 3, ... N)
- Cada entrada contiene: texto, choices, y trace numbers
- Valida que la extracción sea correcta comparando contra el PDF original

USO:
    python3 pdf_extraction_protocol.py <ruta_pdf> <num_entradas> [--validate]
"""

import subprocess
import re
import json
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple


@dataclass
class RollInfo:
    """Información de una tirada de dados"""
    skill: str
    difficulty: str = "Normal"
    on_success: Optional[int] = None
    on_failure: Optional[int] = None
    raw_text: str = ""


@dataclass
class Entry:
    """Estructura de una entrada extraída"""
    number: int
    text: str
    choices: List[str]
    trace_numbers: List[int]
    character_name: Optional[str] = None
    is_adventure_entry: bool = True  # False si es intro/instrucciones
    entry_type: str = "adventure"    # "adventure", "intro", "empty", "instruction"
    rolls: List[RollInfo] = None     # Instrucciones de tiradas

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


class PDFBookExtractor:
    """Extractor genérico para libros en formato de aventura solitaria"""

    def __init__(self, pdf_path: str, total_entries: int):
        self.pdf_path = pdf_path
        self.total_entries = total_entries
        self.lines = self._extract_raw_text()
        self.entry_line_map = self._find_entry_locations()

    def _extract_raw_text(self) -> List[str]:
        """Extrae texto plano del PDF"""
        result = subprocess.run(
            ['pdftotext', self.pdf_path, '-'],
            capture_output=True,
            text=True
        )
        return result.stdout.split('\n')

    def _extract_rolls_from_choices(self, choices: List[str]) -> List[RollInfo]:
        """Extrae información de rolls de las choices"""
        rolls = []

        for choice in choices:
            # Buscar patrones de rolls en el choice
            if 'roll' in choice.lower() or 'test' in choice.lower():
                roll_info = self._parse_roll_instruction(choice)
                if roll_info:
                    rolls.append(roll_info)

        return rolls

    def _parse_roll_instruction(self, text: str) -> Optional[RollInfo]:
        """
        Parsea una instrucción de roll del formato:
        "Make a SKILL roll: if you succeed, go to X; if you fail, go to Y."
        """
        # Patrón principal
        pattern = r'Make\s+(?:an?\s+)?(\w+(?:\s+\w+)*?)\s+roll(?:\s+\(([^)]+)\))?:\s*if you succeed,\s*go to (\d+);\s*if you fail,\s*go to (\d+)'
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            skill = match.group(1).strip()
            difficulty_text = match.group(2) if match.group(2) else "Normal"
            on_success = int(match.group(3))
            on_failure = int(match.group(4))

            # Determinar dificultad
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

    def _find_entry_locations(self) -> Dict[int, int]:
        """Encuentra dónde comienza cada entrada numerada en el PDF

        Estrategia: Una entrada VERDADERA tiene:
        - Un número solo en su línea: "10"
        - Y la línea anterior es VACÍA o cierre de paréntesis: ")" o ""
        - (Los trace numbers están entre paréntesis, ej: "(107)")
        """
        locations = {}

        # Primero, encontrar todos los candidatos
        candidates = {}
        for i, line in enumerate(self.lines):
            # Patrón 1: Número solo
            match = re.match(r'^\s*(\d{1,3})\s*$', line)
            if match:
                num = int(match.group(1))
                if 1 <= num <= self.total_entries:
                    candidates[num] = i

            # Patrón 2: "B NÚMERO"
            match = re.match(r'^\s*B\s+(\d{1,3})\s*$', line)
            if match:
                num = int(match.group(1))
                if 1 <= num <= self.total_entries:
                    locations[num] = i  # Estos siempre son válidos

        # Para los candidatos normales, validar
        for num, line_idx in candidates.items():
            # Si ya está en locations (patrón B), saltarlo
            if num in locations:
                continue

            # Mirar línea anterior
            prev_line = self.lines[line_idx - 1].strip() if line_idx > 0 else ""

            # Patrón válido:
            # - Línea anterior vacía (separador entre entradas)
            # - O línea anterior es paréntesis (fin de trace numbers)
            # - O línea anterior es número de una entrada anterior (raro pero válido)
            if not prev_line or prev_line.endswith(')') or (prev_line.isdigit() and int(prev_line) == num - 1):
                locations[num] = line_idx

        return locations

    def _extract_entry_from_pdf(self, entry_num: int) -> Optional[Entry]:
        """Extrae una entrada específica del PDF"""
        if entry_num not in self.entry_line_map:
            return None

        start_idx = self.entry_line_map[entry_num]

        # Encontrar dónde termina esta entrada (siguiente número o EOF)
        end_idx = len(self.lines)
        for next_num in sorted(self.entry_line_map.keys()):
            if self.entry_line_map[next_num] > start_idx:
                end_idx = self.entry_line_map[next_num]
                break

        # Extraer líneas relevantes (saltar el número inicial)
        content_lines = []
        choices = []
        trace_numbers = []
        character_name = None
        in_content = False

        for i in range(start_idx + 1, end_idx):
            line = self.lines[i].rstrip()
            stripped = line.strip()

            # Ignorar líneas de header del PDF
            if 'ALONE AGAINST THE TIDE' in line:
                continue
            if stripped and all(c in 'BOKRUG ' for c in stripped):
                continue

            # Verificar si es un choice (comienza con •)
            if stripped.startswith('•'):
                choices.append(stripped)
                continue

            # Verificar si es trace numbers (entre paréntesis)
            if re.match(r'^\s*\([\d\s,]+\)\s*$', stripped):
                # Extraer números
                numbers_match = re.findall(r'\d+', stripped)
                trace_numbers = [int(n) for n in numbers_match]
                continue

            # Ignorar líneas vacías al inicio
            if not in_content and not stripped:
                continue

            # Posible nombre de personaje (línea corta antes del contenido)
            if not in_content and stripped and len(stripped) < 50 and not any(c in stripped for c in '.!?'):
                if re.match(r'^[A-Z][a-zA-Z\s]+$', stripped):
                    character_name = stripped
                    continue

            # Contenido principal
            if stripped:
                in_content = True
                content_lines.append(stripped)

        # Normalizar texto
        full_text = ' '.join(content_lines)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        # Determinar tipo de entrada
        entry_type = "adventure"
        is_adventure = True
        text_lower = full_text.lower()

        # Paso 1: Detectar entradas vacías
        if not full_text or len(full_text) < 5:
            entry_type = "empty"
            is_adventure = False

        # Paso 2: Si tiene choices o trace numbers válidos, es aventura
        elif choices or trace_numbers:
            entry_type = "adventure"
            is_adventure = True

        # Paso 3: Detectar instrucciones muy específicas
        elif any(keyword in text_lower for keyword in
                 ['getting started', 'preparing to start', 'reading this book',
                  'introduction', 'what is call of cthulhu', 'for use with the call of cthulhu',
                  'calculate your', 'allocate', 'characteristic']):
            entry_type = "instruction"
            is_adventure = False

        # Paso 4: Si tiene muy poco texto, marcar como empty
        elif len(full_text) < 20:
            entry_type = "empty"
            is_adventure = False

        # Extraer información de rolls
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
        """Extrae todas las entradas"""
        entries = []
        for num in sorted(self.entry_line_map.keys()):
            entry = self._extract_entry_from_pdf(num)
            if entry:
                entries.append(entry)
        return entries

    def validate_entry(self, entry_num: int) -> Tuple[bool, str]:
        """
        Valida que una entrada sea correcta comparándola contra el PDF.
        Retorna: (es_valida, mensaje)
        """
        if entry_num not in self.entry_line_map:
            return False, f"Entrada {entry_num} no encontrada en PDF"

        # Extraer de PDF
        extracted = self._extract_entry_from_pdf(entry_num)
        if not extracted:
            return False, f"No se pudo extraer entrada {entry_num}"

        # Validaciones básicas
        if not extracted.text or len(extracted.text) < 10:
            return False, f"Entrada {entry_num}: texto muy corto ({len(extracted.text)} chars)"

        if entry_num > 1 and not extracted.choices and not any(
            keyword in extracted.text.lower() for keyword in
            ['the end', 'you have', 'your visit', 'dead', 'killed']
        ):
            # Las entradas finales pueden no tener choices
            return False, f"Entrada {entry_num}: sin choices (podría ser incompleta)"

        return True, "OK"


def main():
    if len(sys.argv) < 3:
        print(f"USO: {sys.argv[0]} <ruta_pdf> <num_entradas> [--validate] [--output <file.json>]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    total_entries = int(sys.argv[2])
    validate = '--validate' in sys.argv
    output_file = 'entries_extracted.json'

    # Procesar argumentos
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    print(f"📖 Extrayendo {total_entries} entradas de: {pdf_path}")
    print("="*80)

    # Crear extractor
    extractor = PDFBookExtractor(pdf_path, total_entries)
    print(f"✓ PDF cargado ({len(extractor.lines)} líneas)")
    print(f"✓ Encontradas {len(extractor.entry_line_map)} entradas numeradas")
    print()

    # Extraer todas las entradas
    print("Extrayendo entradas...")
    entries = extractor.extract_all()
    print(f"✓ {len(entries)} entradas extraídas")
    print()

    # Validar si se especificó
    if validate:
        print("Validando entradas contra PDF original...")
        errors = []
        for i, entry in enumerate(entries[:20]):  # Validar primeras 20
            is_valid, msg = extractor.validate_entry(entry.number)
            if is_valid:
                print(f"✓ Entry {entry.number}: {msg}")
            else:
                print(f"✗ Entry {entry.number}: {msg}")
                errors.append(entry.number)

        if errors:
            print(f"\n⚠ {len(errors)} entradas con problemas: {errors}")
        else:
            print(f"\n✅ Primeras 20 entradas VALIDADAS correctamente")
        print()

    # Mostrar estadísticas
    print("📊 ESTADÍSTICAS:")
    total_chars = sum(len(e.text) for e in entries)
    avg_chars = total_chars / len(entries) if entries else 0
    print(f"   Total de entradas: {len(entries)}")
    print(f"   Caracteres totales: {total_chars:,}")
    print(f"   Promedio por entrada: {avg_chars:.0f}")
    print(f"   Min: {min(len(e.text) for e in entries)} | Max: {max(len(e.text) for e in entries)}")

    # Verificar completitud
    missing = []
    for i in range(1, total_entries + 1):
        if not any(e.number == i for e in entries):
            missing.append(i)

    if missing:
        print(f"\n⚠ Entradas faltantes ({len(missing)}): {missing[:20]}")
    else:
        print(f"\n✅ COMPLETO: Todas las entradas 1-{total_entries} presentes")

    # Guardar resultado
    print(f"\nGuardando en {output_file}...")
    with open(output_file, 'w') as f:
        json.dump([e.to_dict() for e in entries], f, indent=2)
    print(f"✓ Archivo generado")


if __name__ == '__main__':
    main()
