#!/usr/bin/env python3
"""
Extrae sección de HANDOUTS de "Alone Against the Dark"
"""

import subprocess
import re

result = subprocess.run(
    ['pdftotext', '/Users/adrianmedina/src/Cthulhu/toaz.info-call-of-cthulhu-alone-against-the-dark-2017-pr_957240174eca06fce7a47b8884b2fc5f.pdf', '-'],
    capture_output=True,
    text=True
)
text = result.stdout
lines = result.stdout.split('\n')

print("=" * 80)
print("EXTRAYENDO SECCIÓN HANDOUTS")
print("=" * 80)

# Buscar "HANDOUT"
handout_lines = []
for i, line in enumerate(lines):
    if 'HANDOUT' in line.upper():
        handout_lines.append((i, line))

print(f"\n✓ Encontradas {len(handout_lines)} líneas con 'HANDOUT'")

# Mostrar contexto
if handout_lines:
    print("\nPrimeras menciones:")
    for line_no, line in handout_lines[:5]:
        print(f"  Línea {line_no}: {line[:80]}")

# Buscar dónde COMIENZA la sección de handouts (típicamente después de las entradas)
print("\n" + "=" * 80)
print("ANALIZANDO ESTRUCTURA")
print("=" * 80)

# Buscar líneas que marcan secciones
section_markers = []
for i, line in enumerate(lines):
    if re.search(r'(CHARACTER SHEET|INVESTIGATOR|HANDOUT|APPENDIX)', line.upper()):
        section_markers.append((i, line.strip()[:60]))

print(f"Marcadores de sección encontrados:")
for line_no, content in section_markers[:10]:
    print(f"  Línea {line_no}: {content}")

# Buscar sección de investigadores (puede estar cerca de handouts)
print("\n" + "=" * 80)
print("BUSCANDO DATOS DE INVESTIGADORES")
print("=" * 80)

# Patrones típicos
inv_names = ['Ernest Holt', 'Lydia Lau', 'Lt. Devon Wilson', 'Professor Louis Grunewald',
             'Professor Grunewald', 'Grunewald']

for name in inv_names:
    matches = [(i, lines[i]) for i, line in enumerate(lines) if name.lower() in line.lower()]
    if matches:
        print(f"\n{name}: {len(matches)} menciones")
        for line_no, line in matches[:2]:
            print(f"  Línea {line_no}: {line[:80]}")

# Buscar sección de habilidades genéricas
print("\n" + "=" * 80)
print("DATOS DE HABILIDADES")
print("=" * 80)

skills_found = {}
skill_pattern = r'(\w+(?:\s+\w+)?):\s*(\d+)%'

for i, line in enumerate(lines[-1000:]):  # Últimas 1000 líneas (probablemente handouts)
    matches = re.findall(skill_pattern, line)
    for skill, value in matches:
        if skill not in ['STR', 'CON', 'DEX', 'APP', 'POW', 'SIZ', 'INT', 'EDU']:
            skills_found[skill] = int(value)

print(f"Skills encontradas en últimas 1000 líneas: {len(skills_found)}")
if skills_found:
    for skill, value in sorted(skills_found.items())[:10]:
        print(f"  {skill}: {value}%")
