#!/usr/bin/env python3
"""
PROCESAMIENTO DE PÁGINAS EXTRAÍDAS
1. Espera a que pdftoppm complete
2. Lee cada página PNG
3. OCR para obtener texto
4. Extrae entradas y las agrupa
5. Guarda ilustraciones aparte
6. Compila JSON final con 594 entradas
"""

import subprocess
import json
import os
import re
from pathlib import Path
from collections import defaultdict

PDF_PAGES_DIR = '/Users/adrianmedina/src/Cthulhu/pdf_pages'
ILLUSTRATIONS_DIR = '/Users/adrianmedina/src/Cthulhu/pdf_illustrations'
OUTPUT_JSON = '/Users/adrianmedina/src/Cthulhu/entries_dark_594_complete.json'

def wait_for_extraction():
    """Espera a que pdftoppm termine"""
    print("Esperando extracción de páginas...")
    while True:
        pages = list(Path(PDF_PAGES_DIR).glob('page-*.png'))
        if pages:
            print(f"  ✓ {len(pages)} páginas encontradas")
            return len(pages)
        else:
            import time
            time.sleep(5)
            print("  ... aún en progreso")

def ocr_page(page_num, page_path):
    """OCR una página"""
    ocr_output = f'/tmp/ocr-page-{page_num}'
    
    result = subprocess.run(
        ['tesseract', str(page_path), ocr_output, '-q'],
        capture_output=True,
        text=True
    )
    
    txt_path = f'{ocr_output}.txt'
    if os.path.exists(txt_path):
        with open(txt_path, 'r') as f:
            return f.read()
    return None

def extract_entries_from_text(text, page_num):
    """Extrae entradas del texto OCR de una página"""
    entries = {}
    
    # Patrón: número en su propia línea seguido de contenido
    # Buscar "número\n contenido...\n número"
    
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Detectar número de entrada (1-594)
        if re.match(r'^\d{1,3}$', line):
            entry_num = int(line)
            if 1 <= entry_num <= 594:
                # Recolectar contenido hasta siguiente número
                content_lines = []
                i += 1
                
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # Parar si encontramos siguiente entrada
                    if re.match(r'^\d{1,3}$', next_line) and int(next_line) > entry_num:
                        break
                    
                    if next_line and 'ALONE AGAINST' not in next_line:
                        content_lines.append(next_line)
                    
                    i += 1
                
                content = ' '.join(content_lines)
                content = re.sub(r'\s+', ' ', content).strip()
                
                if content:
                    entries[entry_num] = {
                        'text': content,
                        'page': page_num,
                        'raw_lines': content_lines
                    }
                
                continue
        
        i += 1
    
    return entries

def process_all_pages():
    """Procesa todas las páginas extraídas"""
    
    print("\n" + "=" * 80)
    print("PROCESANDO PÁGINAS EXTRAÍDAS")
    print("=" * 80)
    
    all_entries = {}
    pages = sorted(list(Path(PDF_PAGES_DIR).glob('page-*.png')))
    
    print(f"\nProcesando {len(pages)} páginas...")
    
    for page_idx, page_path in enumerate(pages):
        if page_idx % 10 == 0:
            print(f"  {page_idx}/{len(pages)}...")
        
        # OCR
        ocr_text = ocr_page(page_idx, page_path)
        if not ocr_text:
            continue
        
        # Extraer entradas
        entries = extract_entries_from_text(ocr_text, page_idx)
        all_entries.update(entries)
    
    print(f"\n✓ Extraídas {len(all_entries)} entradas únicamente de páginas")
    
    # Combinar con las 527 ya extraídas
    print("\nCombinando con entradas existentes...")
    
    with open('/Users/adrianmedina/src/Cthulhu/entries_dark_flexible.json', 'r') as f:
        existing = {e['number']: e for e in json.load(f)}
    
    print(f"  Existentes: {len(existing)}")
    print(f"  De OCR: {len(all_entries)}")
    
    # Compilar final (existentes + nuevas)
    final_entries = []
    
    for num in range(1, 595):
        if num in existing:
            entry = existing[num].copy()
        elif num in all_entries:
            entry = {
                'number': num,
                'text': all_entries[num]['text'],
                'choices': [],
                'trace_numbers': [],
                'character_name': None,
                'is_adventure_entry': len(all_entries[num]['text']) > 20,
                'entry_type': 'adventure',
                'rolls': []
            }
        else:
            # Placeholder
            entry = {
                'number': num,
                'text': f'[ENTRADA {num} - No encontrada]',
                'choices': [],
                'trace_numbers': [],
                'character_name': None,
                'is_adventure_entry': False,
                'entry_type': 'placeholder',
                'rolls': []
            }
        
        final_entries.append(entry)
    
    # Guardar
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(final_entries, f, indent=2)
    
    print(f"\n✓ Guardado: {OUTPUT_JSON}")
    
    # Estadísticas
    with_content = len([e for e in final_entries if e['entry_type'] != 'placeholder'])
    print(f"\nESTADÍSTICAS FINALES:")
    print(f"  Total: {len(final_entries)}")
    print(f"  Con contenido: {with_content}")
    print(f"  Placeholders: {len(final_entries) - with_content}")

if __name__ == '__main__':
    num_pages = wait_for_extraction()
    process_all_pages()
