#!/usr/bin/env python3
"""
PROTOCOLO DE BÚSQUEDA INTELIGENTE
Para cada entrada faltante:
1. Encuentra dónde está la entrada anterior/siguiente
2. Extrae las páginas en ese rango
3. Lee las imágenes para encontrar la entrada
"""

import subprocess
import re
import json
import os
from pathlib import Path

# Paso 1: Mapear página de cada entrada existente
print("=" * 80)
print("PASO 1: Extrayendo PDF y mapeando páginas")
print("=" * 80)

result = subprocess.run(
    ['pdftotext', 
     '/Users/adrianmedina/src/Cthulhu/toaz.info-call-of-cthulhu-alone-against-the-dark-2017-pr_957240174eca06fce7a47b8884b2fc5f.pdf',
     '-'],
    capture_output=True,
    text=True
)

lines = result.stdout.split('\n')

# Mapear página de cada entrada
entry_to_line = {}
for i, line in enumerate(lines):
    match = re.match(r'^\s*(\d{1,3})\s*$', line.strip())
    if match:
        num = int(match.group(1))
        if 1 <= num <= 594:
            entry_to_line[num] = i

print(f"Entradas encontradas: {len(entry_to_line)}")

# Estimar líneas por página (típicamente 30-40 líneas por página)
lines_per_page = 40
entry_to_page = {num: line // lines_per_page for num, line in entry_to_line.items()}

print(f"Mapeadas a páginas (estimado)")

# Paso 2: Para cada entrada faltante, encontrar rango
print("\n" + "=" * 80)
print("PASO 2: Identificando páginas de entradas faltantes")
print("=" * 80)

with open('entries_dark_594.json', 'r') as f:
    all_entries = json.load(f)

missing_nums = [e['number'] for e in all_entries if e['entry_type'] == 'placeholder']
print(f"Entradas faltantes: {len(missing_nums)}")

# Para cada faltante, encontrar rango
missing_pages = {}
for num in missing_nums:
    # Buscar entrada anterior y siguiente que existan
    prev_num = num - 1
    next_num = num + 1
    
    while prev_num > 0 and prev_num not in entry_to_page:
        prev_num -= 1
    
    while next_num <= 594 and next_num not in entry_to_page:
        next_num += 1
    
    if prev_num in entry_to_page and next_num in entry_to_page:
        prev_page = entry_to_page[prev_num]
        next_page = entry_to_page[next_num]
        
        # Buscar en rango entre las páginas
        search_pages = list(range(prev_page, next_page + 1))
        missing_pages[num] = {
            'between': (prev_num, next_num),
            'pages': search_pages,
            'count': len(search_pages)
        }

print(f"\nRangos identificados:")
for num in sorted(missing_nums[:10]):
    if num in missing_pages:
        info = missing_pages[num]
        print(f"  Entry {num}: entre {info['between'][0]}-{info['between'][1]} → páginas {info['pages'][:3]}")

# Paso 3: Mostrar protocolo
print("\n" + "=" * 80)
print("PROTOCOLO DE EXTRACCIÓN")
print("=" * 80)

print(f"""
Para cada entrada faltante:

1. Identificar entradas anterior/siguiente (que SÍ existan)
2. Determinar rango de páginas entre ellas
3. Extraer esas páginas como PNG
4. Leer las imágenes para encontrar la entrada
5. Parsear contenido

Ejemplo: Entry 111
  - Anterior: Entry 110 (página ~9)
  - Siguiente: Entry 112 (página ~10)
  - Buscar: páginas 9-10
  - Leer imagen
  - Encontrar y parsear Entry 111

Ventaja: Búsqueda targetizada, no todo el PDF
""")

# Guardar mapeo
with open('/tmp/entry_page_map.json', 'w') as f:
    json.dump({
        'entry_to_page': {str(k): v for k, v in entry_to_page.items()},
        'missing_pages': {str(k): v for k, v in missing_pages.items()}
    }, f, indent=2)

print("✓ Mapeo guardado en entry_page_map.json")
