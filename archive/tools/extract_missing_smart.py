#!/usr/bin/env python3
"""
EXTRACCIÓN INTELIGENTE DE ENTRADAS FALTANTES
1. Identifica rango de páginas para cada entrada faltante
2. Extrae página como imagen con pdftoppm
3. OCR con tesseract
4. Parsea el contenido
5. Inserta en JSON
"""

import subprocess
import re
import json
import os
from pathlib import Path

PDF_PATH = '/Users/adrianmedina/src/Cthulhu/toaz.info-call-of-cthulhu-alone-against-the-dark-2017-pr_957240174eca06fce7a47b8884b2fc5f.pdf'

def get_page_for_entry(entry_num, pdf_path):
    """Encuentra qué página contiene una entrada"""
    # Extraer texto del PDF
    result = subprocess.run(
        ['pdftotext', pdf_path, '-'],
        capture_output=True,
        text=True
    )
    
    lines = result.stdout.split('\n')
    
    # Buscar número de entrada
    for i, line in enumerate(lines):
        if re.search(rf'\b{entry_num}\b', line):
            # Estimar página (35 líneas/página aprox)
            page = i // 35
            return page
    
    return None

def extract_entry_ocr(entry_num, page_num):
    """Extrae contenido de entrada usando OCR"""
    
    # Extraer página como imagen
    img_path = f'/tmp/entry-{entry_num}-page-{page_num}.png'
    cmd = ['pdftoppm', '-png', '-singlefile', 
           '-f', str(page_num), '-l', str(page_num),
           PDF_PATH, img_path.replace('.png', '')]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    
    # OCR
    ocr_path = f'/tmp/ocr-{entry_num}'
    cmd = ['tesseract', img_path, ocr_path, '-q']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Leer resultado
    txt_path = ocr_path + '.txt'
    if not os.path.exists(txt_path):
        return None
    
    with open(txt_path, 'r') as f:
        ocr_text = f.read()
    
    # Parsear entrada del OCR
    entry_pattern = rf'{entry_num}\s*\n(.*?)(?=\n\n(?:ALONE|$|\d{{2,3}}\s*\n))'
    match = re.search(entry_pattern, ocr_text, re.DOTALL)
    
    if match:
        content = match.group(1).strip()
        # Limpiar
        content = re.sub(r'\s+', ' ', content)
        return content
    
    return None

def extract_all_missing():
    """Extrae todas las entradas faltantes"""
    
    print("=" * 80)
    print("EXTRACCIÓN INTELIGENTE DE ENTRADAS FALTANTES")
    print("=" * 80)
    
    with open('entries_dark_594.json', 'r') as f:
        entries = json.load(f)
    
    missing_nums = [e['number'] for e in entries if e['entry_type'] == 'placeholder']
    
    print(f"\n{len(missing_nums)} entradas a extraer")
    print(f"Esto puede tomar varios minutos...")
    
    extracted = {}
    for i, num in enumerate(missing_nums):
        if i % 10 == 0:
            print(f"\n Progreso: {i}/{len(missing_nums)}")
        
        # Encontrar página
        page = get_page_for_entry(num, PDF_PATH)
        if page is None:
            print(f"  ✗ {num}: no se encontró página")
            continue
        
        # Extraer con OCR
        content = extract_entry_ocr(num, page)
        if content:
            extracted[num] = content
            print(f"  ✓ {num}")
        else:
            print(f"  ✗ {num}: OCR falló")
    
    print(f"\n{'='*80}")
    print(f"Extraídas: {len(extracted)}/{len(missing_nums)}")
    
    # Actualizar JSON
    if extracted:
        for entry in entries:
            if entry['number'] in extracted:
                entry['text'] = extracted[entry['number']]
                entry['entry_type'] = 'adventure'
        
        with open('entries_dark_594_complete.json', 'w') as f:
            json.dump(entries, f, indent=2)
        
        print(f"✓ Guardado: entries_dark_594_complete.json")
        return True
    
    return False

if __name__ == '__main__':
    extract_all_missing()
