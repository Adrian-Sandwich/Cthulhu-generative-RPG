#!/usr/bin/env python3
"""
EXTRACCIÓN INTELIGENTE CON OCR
Para cada página PNG:
1. Hacer OCR completo
2. Buscar entradas faltantes en el OCR
3. Extraer y limpiar su contenido
4. Compilar JSON
"""

import subprocess
import re
import json
import os
from pathlib import Path

PDF_PAGES_DIR = '/Users/adrianmedina/src/Cthulhu/pdf_pages'
OUTPUT_JSON = '/Users/adrianmedina/src/Cthulhu/entries_dark_594_final.json'

def ocr_page(page_num):
    """OCR una página PNG"""
    page_path = f'{PDF_PAGES_DIR}/page-{page_num:03d}.png'
    
    if not os.path.exists(page_path):
        return None
    
    ocr_output = f'/tmp/ocr-smart-{page_num}'
    
    # OCR
    result = subprocess.run(
        ['tesseract', page_path, ocr_output, '-q'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    txt_path = f'{ocr_output}.txt'
    if os.path.exists(txt_path):
        with open(txt_path, 'r') as f:
            return f.read()
    
    return None

def extract_entries_from_ocr(ocr_text, page_num):
    """Extrae entradas del OCR"""
    entries = {}
    
    # Buscar patrones: "número\ncontenido...\nnúmero"
    # Numerador de entrada (1-594)
    pattern = r'^(\d{1,3})\s*\n(.*?)(?=^\d{1,3}\s*\n|$)'
    
    matches = re.finditer(pattern, ocr_text, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        try:
            entry_num = int(match.group(1))
            
            if 1 <= entry_num <= 594:
                content = match.group(2).strip()
                
                # Limpiar
                content = re.sub(r'\s+', ' ', content)
                content = re.sub(r'[^\w\s\(\),;\.\-\'\":]', '', content)  # Solo caracteres válidos
                
                if len(content) > 10:  # Solo si hay contenido significativo
                    entries[entry_num] = {
                        'text': content,
                        'page': page_num
                    }
        except:
            pass
    
    return entries

def process_all_pages_ocr():
    """Procesa todas las páginas con OCR"""
    
    print("=" * 80)
    print("EXTRACCIÓN CON OCR INTELIGENTE")
    print("=" * 80)
    
    all_entries_ocr = {}
    total_pages = len(list(Path(PDF_PAGES_DIR).glob('page-*.png')))
    
    print(f"\nProcesando {total_pages} páginas...")
    
    for page_num in range(1, total_pages + 1):
        if page_num % 10 == 0:
            print(f"  {page_num}/{total_pages}...")
        
        ocr_text = ocr_page(page_num)
        if not ocr_text:
            continue
        
        entries = extract_entries_from_ocr(ocr_text, page_num)
        all_entries_ocr.update(entries)
    
    print(f"\n✓ Extraídas {len(all_entries_ocr)} entradas de OCR")
    return all_entries_ocr

def compile_final_json():
    """Compila JSON final"""
    
    # Cargar existentes
    with open('/Users/adrianmedina/src/Cthulhu/entries_dark_flexible.json', 'r') as f:
        existing = {e['number']: e for e in json.load(f)}
    
    print(f"Entradas existentes: {len(existing)}")
    
    # OCR
    ocr_entries = process_all_pages_ocr()
    
    # Compilar final
    final_entries = []
    
    for num in range(1, 595):
        if num in existing:
            entry = existing[num].copy()
        elif num in ocr_entries:
            entry = {
                'number': num,
                'text': ocr_entries[num]['text'],
                'choices': [],
                'trace_numbers': [],
                'character_name': None,
                'is_adventure_entry': len(ocr_entries[num]['text']) > 20,
                'entry_type': 'adventure',
                'rolls': []
            }
        else:
            entry = {
                'number': num,
                'text': f'[Entrada {num} no encontrada]',
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
    print(f"  Con contenido: {with_content}/594")
    print(f"  Placeholders: {len(final_entries) - with_content}")

if __name__ == '__main__':
    compile_final_json()
