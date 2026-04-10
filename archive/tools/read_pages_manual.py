#!/usr/bin/env python3
"""
LECTURA MANUAL PÁGINA POR PÁGINA
Lee imágenes PNG y extrae texto visualmente
Guarda ilustraciones en carpeta aparte
"""

import json
import os
import re
from pathlib import Path

print("=" * 80)
print("PROTOCOLO: LECTURA MANUAL DE PÁGINAS")
print("=" * 80)

print("""
Proceso:
1. Leer cada PNG página por página
2. Extraer texto de entradas (números + contenido)
3. Identificar ilustraciones (guardar en carpeta aparte)
4. Compilar JSON con todas las 594 entradas

Estructura de carpetas:
  pdf_pages/          → Páginas completas (referencia)
  pdf_illustrations/  → Ilustraciones por entrada
  entries_dark_594_complete.json → JSON final

Convención de nombres:
  pdf_illustrations/entry-111.png
  pdf_illustrations/entry-154-alt.png (si hay múltiples)
""")

print("\nEsperando extracción de páginas...")
print("Una vez completado:")
print("  1. Leeré cada página PNG")
print("  2. Extraeré el texto de entradas")
print("  3. Separaré ilustraciones")
print("  4. Compilaré JSON final")
