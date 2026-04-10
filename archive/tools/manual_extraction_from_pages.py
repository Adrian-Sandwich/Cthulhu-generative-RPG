#!/usr/bin/env python3
"""
EXTRACCIÓN MANUAL DESDE IMÁGENES PNG
Lee cada página visualmente y extrae entradas manualmente
(El usuario podría hacer esto, o usamos un proceso semi-automático)

Proceso:
1. Para cada página PNG, mostrar qué entradas contiene
2. Leer manualmente (o con mejor OCR)
3. Extraer contenido
4. Guardar ilustraciones
5. Compilar JSON
"""

import json
import re
from pathlib import Path

# Cargar entradas existentes
with open('entries_dark_flexible.json', 'r') as f:
    existing = {e['number']: e for e in json.load(f)}

print("=" * 80)
print("EXTRACCIÓN MANUAL DESDE IMÁGENES")
print("=" * 80)

print(f"\nEntradas existentes: {len(existing)}")
print("Entradas faltantes: 67")
print("\nPROCESO:")
print("1. Leer cada página PNG")
print("2. Identificar qué entradas contiene")
print("3. Para faltantes, extraer manualmente el texto")
print("4. Guardar ilustraciones en carpeta aparte")
print("5. Compilar JSON final")

# Mapeo manual de qué páginas tienen qué entradas
# Basado en lectura visual anterior
page_entries = {
    25: list(range(94, 101)),    # Página 25: entries 94-100
    27: list(range(111, 118)),   # Página 27: entries 111-117 (FALTANTES)
    # Continuar mapeando...
}

print("\nPáginas identificadas con entradas faltantes:")
missing_nums = set(range(1, 595)) - set(existing.keys())
print(f"  Faltantes: {sorted(missing_nums)[:20]}...")

# Para hacer esto correctamente, necesitaríamos:
# 1. Leer cada PNG
# 2. Determinar con OCR/visión qué entradas contiene
# 3. Para las faltantes, extraer el contenido
# 4. Guardar ilustraciones asociadas

print("\n" + "=" * 80)
print("PRÓXIMO PASO:")
print("=" * 80)
print("""
Opciones:

A) Lectura manual del usuario:
   - Abrir PDF
   - Para cada entrada faltante, copiar su contenido
   - Pasar a script de compilación

B) Lectura automática mejorada:
   - Usar mejor OCR en regiones específicas
   - Focus en páginas 27-35 donde están las primeras faltantes
   - Extraer automáticamente

C) Lectura por usuario páginas específicas:
   - Mostrar imagen de página
   - Usuario copia contenido manualmente
   - Script compila

¿Cuál prefieres?
""")

# Si el usuario proporciona entradas faltantes manualmente:
# Se compilarían así:

sample_missing = {
    111: "The film today is Alfred Hitchcock's Murder. You look forward to seeing the film and feel that young Hesscock is a promising protege...",
    112: "If any of your rolls were successful, read the appropriate entry below. If all your rolls were unsuccessful, you didn't roll the appropriate entry below...",
}

print("\nFormato para proporcionar entradas faltantes:")
print(json.dumps(sample_missing, indent=2, ensure_ascii=False))

