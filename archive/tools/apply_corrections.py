#!/usr/bin/env python3
"""
APLICAR CORRECCIONES A ENTRIES

Lee el archivo de correcciones generado por el validador
y actualiza entries_with_rolls.json
"""

import json
from typing import Dict, List


def apply_corrections(json_file: str, corrections_file: str, output_file: str = None):
    """Aplica correcciones al JSON"""

    if output_file is None:
        output_file = json_file

    # Cargar datos
    with open(json_file, 'r') as f:
        entries = json.load(f)

    with open(corrections_file, 'r') as f:
        corrections = json.load(f)

    # Crear mapa de entries
    entry_map = {e['number']: e for e in entries}

    print(f"APLICANDO CORRECCIONES")
    print("="*80)
    print(f"Entries en JSON: {len(entries)}")
    print(f"Correcciones a aplicar: {len(corrections)}")

    applied = 0
    added = 0
    failed = 0

    for correction in corrections:
        entry_num = correction.get('entry')

        if 'action' in correction and correction['action'] == 'ADD_FROM_PDF':
            # Agregar nueva entrada
            new_entry = {
                'number': entry_num,
                'text': correction.get('content', ''),
                'choices': [],
                'trace_numbers': [],
                'character_name': None,
                'is_adventure_entry': True,
                'entry_type': 'adventure',
                'rolls': []
            }

            if entry_num not in entry_map:
                entries.append(new_entry)
                entry_map[entry_num] = new_entry
                added += 1
                print(f"✓ Agregada entrada {entry_num}")
            else:
                failed += 1

        elif 'suggested' in correction:
            # Corregir entrada existente
            if entry_num in entry_map:
                entry_map[entry_num]['text'] = correction['suggested']
                applied += 1
                print(f"✓ Corregida entrada {entry_num}")
            else:
                failed += 1

    # Reordenar por número
    entries = sorted(entry_map.values(), key=lambda e: e['number'])

    # Guardar
    with open(output_file, 'w') as f:
        json.dump(entries, f, indent=2)

    print("\n" + "="*80)
    print(f"RESULTADOS:")
    print(f"  Aplicadas: {applied}")
    print(f"  Agregadas: {added}")
    print(f"  Fallos: {failed}")
    print(f"  Total final: {len(entries)}")
    print(f"\n✓ Guardado en {output_file}")


if __name__ == '__main__':
    apply_corrections('entries_with_rolls.json', 'corrections.json', 'entries_corrected.json')
