#!/usr/bin/env python3
"""
EXTRACCIÓN FINAL OPTIMIZADA
1. OCR en todas las páginas con preprocessing
2. Lectura visual manual para correcciones
3. Compilar JSON 594 completo
"""

import subprocess
import json
import re
from pathlib import Path

def ocr_page_enhanced(page_num):
    """OCR mejorado con preprocessing"""
    page_path = f'/Users/adrianmedina/src/Cthulhu/pdf_pages/page-{page_num:03d}.png'
    
    if not Path(page_path).exists():
        return None
    
    ocr_out = f'/tmp/final-ocr-{page_num}'
    
    # OCR con mejor configuración
    result = subprocess.run(
        ['tesseract', page_path, ocr_out, '--psm', '3', '-c', 'tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ()-,.:;\'\"'],
        capture_output=True,
        text=True,
        timeout=15
    )
    
    txt_path = f'{ocr_out}.txt'
    if Path(txt_path).exists():
        with open(txt_path, 'r') as f:
            return f.read()
    
    return None

def parse_entries_from_ocr(ocr_text):
    """Parse entradas del OCR con mejor regex"""
    entries = {}
    
    # Pattern más tolerante
    # Buscar: número (solos o inicio de línea) seguido de contenido
    lines = ocr_text.split('\n')
    current_entry = None
    current_content = []
    
    for line in lines:
        stripped = line.strip()
        
        # ¿Es un número de entrada?
        if re.match(r'^(\d{1,3})$', stripped):
            entry_num = int(stripped)
            
            # Guardar entrada anterior si existe
            if current_entry and current_content:
                content = ' '.join(current_content)
                content = re.sub(r'\s+', ' ', content).strip()
                if len(content) > 5:
                    entries[current_entry] = content
            
            # Nueva entrada
            current_entry = entry_num
            current_content = []
        elif current_entry and stripped:
            # Agregar a contenido
            current_content.append(stripped)
    
    # Guardar última entrada
    if current_entry and current_content:
        content = ' '.join(current_content)
        content = re.sub(r'\s+', ' ', content).strip()
        if len(content) > 5:
            entries[current_entry] = content
    
    return entries

def main():
    print("=" * 80)
    print("EXTRACCIÓN FINAL CON OCR MEJORADO")
    print("=" * 80)
    
    # Cargar existentes
    with open('/Users/adrianmedina/src/Cthulhu/entries_dark_flexible.json', 'r') as f:
        existing = {e['number']: e for e in json.load(f)}
    
    print(f"\nEntradas existentes: {len(existing)}")
    
    # OCR en todas las páginas
    all_ocr_entries = {}
    pdf_dir = Path('/Users/adrianmedina/src/Cthulhu/pdf_pages')
    pages = sorted(list(pdf_dir.glob('page-*.png')))
    
    print(f"OCR en {len(pages)} páginas...")
    
    for i, page_path in enumerate(pages):
        if i % 20 == 0:
            print(f"  {i+1}/{len(pages)}...")
        
        page_num = int(page_path.stem.split('-')[1])
        
        ocr_text = ocr_page_enhanced(page_num)
        if not ocr_text:
            continue
        
        entries = parse_entries_from_ocr(ocr_text)
        all_ocr_entries.update(entries)
    
    print(f"\n✓ Extraídas {len(all_ocr_entries)} entradas de OCR")
    
    # Compilar final
    print("\nCompilando JSON final...")
    final_entries = []
    
    for num in range(1, 595):
        if num in existing:
            entry = existing[num].copy()
        elif num in all_ocr_entries:
            entry = {
                'number': num,
                'text': all_ocr_entries[num],
                'choices': [],
                'trace_numbers': [],
                'character_name': None,
                'is_adventure_entry': len(all_ocr_entries[num]) > 10,
                'entry_type': 'adventure',
                'rolls': []
            }
        else:
            entry = {
                'number': num,
                'text': f'[ENTRADA {num} - NO ENCONTRADA]',
                'choices': [],
                'trace_numbers': [],
                'character_name': None,
                'is_adventure_entry': False,
                'entry_type': 'placeholder',
                'rolls': []
            }
        
        final_entries.append(entry)
    
    # Guardar
    output = '/Users/adrianmedina/src/Cthulhu/entries_dark_594_final.json'
    with open(output, 'w') as f:
        json.dump(final_entries, f, indent=2)
    
    print(f"✓ Guardado: {output}")
    
    # Estadísticas
    with_content = len([e for e in final_entries if e['entry_type'] != 'placeholder'])
    remaining = len(final_entries) - with_content
    
    print(f"\n{'='*80}")
    print(f"ESTADÍSTICAS FINALES:")
    print(f"  Total entradas: {len(final_entries)}")
    print(f"  Con contenido: {with_content}")
    print(f"  Placeholders: {remaining}")
    
    if remaining > 0:
        missing_nums = [e['number'] for e in final_entries if e['entry_type'] == 'placeholder']
        print(f"\n  Aún faltantes ({remaining}): {missing_nums[:30]}...")

if __name__ == '__main__':
    main()
