#!/usr/bin/env python3
"""
VALIDADOR FINAL - SIN DEPENDENCIAS EXTERNAS
"""

import json
import subprocess
import re
from typing import Dict, Tuple


class FinalValidator:
    """Validador que no requiere dependencias externas"""

    def __init__(self, json_file: str, pdf_file: str):
        # Cargar JSON
        with open(json_file, 'r') as f:
            self.json_entries = json.load(f)

        # Extraer PDF
        result = subprocess.run(
            ['pdftotext', pdf_file, '-'],
            capture_output=True,
            text=True
        )
        self.pdf_lines = result.stdout.split('\n')

        self.json_map = {e['number']: e for e in self.json_entries}
        self.pdf_entries = self._extract_pdf_entries()

        print(f"✓ JSON: {len(self.json_entries)} entradas")
        print(f"✓ PDF: {len(self.pdf_entries)} entradas")

    def _extract_pdf_entries(self) -> Dict[int, str]:
        """Extrae todas las entries del PDF"""
        entries = {}

        for i, line in enumerate(self.pdf_lines):
            stripped = line.strip()

            # Patrón 1: Número solo
            if re.match(r'^\d{1,3}$', stripped):
                num = int(stripped)
                if 1 <= num <= 243:
                    content = self._get_content(i)
                    if content and len(content) > 20:
                        entries[num] = content

            # Patrón 2: "B NÚMERO"
            elif re.match(r'B\s+(\d{1,3})', stripped):
                match = re.search(r'B\s+(\d{1,3})', stripped)
                if match:
                    num = int(match.group(1))
                    if 1 <= num <= 243:
                        content = self._get_content(i)
                        if content and len(content) > 20:
                            entries[num] = content

        return entries

    def _get_content(self, start_line: int) -> str:
        """Obtiene contenido de una entrada"""
        lines = []
        i = start_line + 1

        while i < len(self.pdf_lines) and len(lines) < 50:
            line = self.pdf_lines[i].strip()

            if not line or re.match(r'^\d{1,3}$', line) or re.match(r'B\s+\d', line):
                break

            if line and 'ALONE AGAINST' not in line:
                lines.append(line)

            i += 1

        return ' '.join(lines).strip()

    def validate_all(self) -> Dict:
        """Valida todas las entradas"""
        stats = {
            'valid': 0,
            'mismatch': 0,
            'missing_in_pdf': 0,
            'extra_in_json': 0,
        }

        mismatches = []

        print("\n🔍 VALIDANDO...")
        print("="*80)

        for entry_num in range(1, 244):
            if entry_num % 50 == 0:
                print(f"  {entry_num}/243...")

            json_entry = self.json_map.get(entry_num)
            pdf_content = self.pdf_entries.get(entry_num)

            # Caso 1: Ambos existen
            if json_entry and pdf_content:
                # Comparar primeras 50 chars
                json_start = re.sub(r'\s+', ' ', json_entry['text'][:70]).lower()
                pdf_start = re.sub(r'\s+', ' ', pdf_content[:70]).lower()

                if json_start == pdf_start or json_start in pdf_start:
                    stats['valid'] += 1
                else:
                    stats['mismatch'] += 1
                    mismatches.append({
                        'entry': entry_num,
                        'json_start': json_start[:50],
                        'pdf_start': pdf_start[:50]
                    })

            # Caso 2: En JSON pero no en PDF
            elif json_entry and not pdf_content:
                stats['extra_in_json'] += 1
                mismatches.append({
                    'entry': entry_num,
                    'issue': 'En JSON pero no en PDF',
                    'json': json_entry['text'][:50]
                })

            # Caso 3: En PDF pero no en JSON
            elif pdf_content and not json_entry:
                stats['missing_in_pdf'] += 1
                mismatches.append({
                    'entry': entry_num,
                    'issue': 'En PDF pero no en JSON',
                    'pdf': pdf_content[:50]
                })

            else:
                stats['valid'] += 1

        return stats, mismatches

    def print_report(self, stats: Dict, mismatches):
        """Genera reporte"""
        print("\n" + "="*80)
        print("REPORTE DE VALIDACIÓN")
        print("="*80)

        total = sum(stats.values())
        print(f"\n📊 RESULTADOS:")
        print(f"  Total validadas: {total}")
        print(f"  ✓ Válidas: {stats['valid']} ({100*stats['valid']//243}%)")
        print(f"  ⚠ Discrepancias: {stats['mismatch']}")
        print(f"  ⚠ En PDF, no en JSON: {stats['missing_in_pdf']}")
        print(f"  ⚠ En JSON, no en PDF: {stats['extra_in_json']}")

        if mismatches:
            print(f"\n⚠️ PROBLEMAS DETECTADOS ({len(mismatches)}):")
            print("-"*80)
            for m in mismatches[:15]:
                print(f"\nEntry {m['entry']}:")
                if 'issue' in m:
                    print(f"  {m['issue']}")
                else:
                    print(f"  JSON: {m['json_start'][:40]}...")
                    print(f"  PDF:  {m['pdf_start'][:40]}...")

            if len(mismatches) > 15:
                print(f"\n... y {len(mismatches)-15} problemas más")
        else:
            print("\n✅ SIN PROBLEMAS DETECTADOS")


if __name__ == '__main__':
    print("✓ VALIDADOR FINAL")
    print("="*80)

    validator = FinalValidator(
        'entries_with_rolls.json',
        '/Users/adrianmedina/src/Cthulhu/toaz.info-alone-against-the-tide-pr_33b3d17a9830aef5793eb045adc40271.pdf'
    )

    stats, mismatches = validator.validate_all()
    validator.print_report(stats, mismatches)

    # Guardar resultados
    with open('final_validation.json', 'w') as f:
        json.dump({
            'stats': stats,
            'problems': mismatches
        }, f, indent=2)

    print(f"\n✓ Guardado en final_validation.json")
