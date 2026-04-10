#!/usr/bin/env python3
"""
Extrae investigadores predefinidos de "Alone Against the Dark"
"""

import subprocess
import re
import json
from dataclasses import dataclass, asdict

@dataclass
class Investigator:
    name: str
    skills: dict  # {skill_name: percentage}
    characteristics: dict  # {STR, CON, DEX, etc: value}
    occupation: str = ""
    background: str = ""

    def to_dict(self):
        return {
            'name': self.name,
            'skills': self.skills,
            'characteristics': self.characteristics,
            'occupation': self.occupation,
            'background': self.background
        }

# Extraer PDF
result = subprocess.run(
    ['pdftotext', '/Users/adrianmedina/src/Cthulhu/toaz.info-call-of-cthulhu-alone-against-the-dark-2017-pr_957240174eca06fce7a47b8884b2fc5f.pdf', '-'],
    capture_output=True,
    text=True
)
text = result.stdout

# Buscar sección de investigadores
print("=" * 80)
print("BUSCANDO INVESTIGADORES PREDEFINIDOS")
print("=" * 80)

# Nombres encontrados en exploración anterior
known_names = ['Ernest Holt', 'Lydia Lau', 'Lt. Devon Wilson', 'Professor Louis Gruenwald']

investigators = []

for name in known_names:
    # Buscar en texto
    if name in text:
        # Encontrar sección alrededor del nombre
        idx = text.find(name)
        section = text[max(0, idx-500):min(len(text), idx+1500)]
        
        print(f"\n✓ {name} encontrado")
        print(f"  Contexto: {section[:200]}...")
        
        # Intentar extraer información
        # Patrón típico: nombre, ocupación, habilidades, características
        
        investigator = Investigator(
            name=name,
            skills={},
            characteristics={},
            occupation="",
            background=""
        )
        
        # Buscar patrones de habilidades (Skill: XX%)
        skill_pattern = r'(\w+(?:\s+\w+)*?):\s*(\d+)%'
        skill_matches = re.findall(skill_pattern, section)
        
        if skill_matches:
            for skill, value in skill_matches:
                # Filtrar skills válidos (no características)
                if skill not in ['STR', 'CON', 'DEX', 'APP', 'POW', 'SIZ', 'INT', 'EDU']:
                    investigator.skills[skill] = int(value)
        
        # Buscar características
        char_pattern = r'(STR|CON|DEX|APP|POW|SIZ|INT|EDU):\s*(\d+)'
        char_matches = re.findall(char_pattern, section)
        
        if char_matches:
            for char, value in char_matches:
                investigator.characteristics[char] = int(value)
        
        print(f"  Skills: {len(investigator.skills)}")
        print(f"  Características: {len(investigator.characteristics)}")
        
        investigators.append(investigator)
    else:
        print(f"✗ {name} NO encontrado")

# Guardar
if investigators:
    with open('investigators_dark.json', 'w') as f:
        json.dump([inv.to_dict() for inv in investigators], f, indent=2)
    
    print(f"\n✓ {len(investigators)} investigadores guardados en investigators_dark.json")
else:
    print("\n⚠ No se encontraron investigadores")

# Búsqueda más flexible
print("\n" + "=" * 80)
print("BÚSQUEDA FLEXIBLE DE SECCIONES CON HABILIDADES")
print("=" * 80)

# Buscar patrones de habilidades distribuidas
lines = text.split('\n')
skill_sections = []

for i, line in enumerate(lines):
    # Buscar líneas con múltiples habilidades
    if re.search(r'(\w+):\s*\d+%', line) and re.search(r'(\w+):\s*\d+%', line * 2):  # Patrón repetido
        skill_sections.append((i, line[:80]))

print(f"Encontradas {len(skill_sections)} líneas con patrones de habilidades")
if skill_sections[:5]:
    for line_no, content in skill_sections[:5]:
        print(f"  Línea {line_no}: {content}")
