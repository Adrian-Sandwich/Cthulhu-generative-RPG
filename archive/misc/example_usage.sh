#!/bin/bash

# EJEMPLO: Uso del Protocolo de Extracción para diferentes libros

echo "════════════════════════════════════════════════════════════════════════════════"
echo "PROTOCOLO DE EXTRACCIÓN: Ejemplos de Uso"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Ejemplo 1: Extractrír "Alone Against the Tide" (243 entradas)
echo "📖 EJEMPLO 1: Alone Against the Tide"
echo "─────────────────────────────────────────────────────────────────────────────────"
echo "Comando:"
echo "  python3 pdf_extraction_protocol.py alone_against_tide.pdf 243 --validate"
echo ""
echo "Resultado esperado:"
echo "  ✓ 243 entradas extraídas"
echo "  ✓ 234 entradas de aventura"
echo "  ✓ 9 pseudo-entradas (vacías/instrucciones)"
echo "  ✓ Archivo: entries_protocol.json"
echo ""

# Ejemplo 2: Pasos para un libro nuevo
echo "📖 EJEMPLO 2: Extraer un nuevo libro"
echo "─────────────────────────────────────────────────────────────────────────────────"
echo "Paso 1: Determinar número de entradas"
echo "  - Abrir el PDF y buscar el número de la última entrada"
echo "  - Ej: Si la última es 'go to 150', usaremos N=150"
echo ""
echo "Paso 2: Ejecutar extractor"
echo "  python3 pdf_extraction_protocol.py mi_libro.pdf 150 --validate"
echo ""
echo "Paso 3: Revisar resultados"
echo "  - Ver entradas de aventura vs pseudo-entradas"
echo "  - Validaciones en stdout"
echo "  - Output en 'entries_protocol.json'"
echo ""

# Ejemplo 3: Procesamiento post-extracción
echo "📖 EJEMPLO 3: Análisis post-extracción"
echo "─────────────────────────────────────────────────────────────────────────────────"
echo "Contar entradas por tipo:"
echo "  python3 -c \""
echo "    import json"
echo "    with open('entries_protocol.json') as f: entries = json.load(f)"
echo "    adventure = [e for e in entries if e['is_adventure_entry']]"
echo "    print(f'Aventura: {len(adventure)} | Total: {len(entries)}')"
echo "  \""
echo ""

# Ejemplo 4: Uso del protocolo para validar
echo "📖 EJEMPLO 4: Validación de integridad"
echo "─────────────────────────────────────────────────────────────────────────────────"
echo "Verificar que todas las referencias (go to X) tienen entrada X:"
echo "  python3 -c \""
echo "    import json, re"
echo "    with open('entries_protocol.json') as f: entries = json.load(f)"
echo "    numbers = {e['number'] for e in entries}"
echo "    for e in entries:"
echo "      refs = re.findall(r'go to (\\d+)', ' '.join(e['choices']))"
echo "      missing = [r for r in refs if int(r) not in numbers]"
echo "      if missing: print(f'Entry {e[\"number\"]}: refs missing {missing}')"
echo "  \""
echo ""

# Ejemplo 5: Estadísticas detalladas
echo "📖 EJEMPLO 5: Estadísticas del libro"
echo "─────────────────────────────────────────────────────────────────────────────────"
cat << 'PYTHON'
python3 << 'EOF'
import json

with open('entries_protocol.json') as f:
    entries = json.load(f)

# Filtrar entradas reales
adventure_entries = [e for e in entries if e['is_adventure_entry']]

# Estadísticas
total_text = sum(len(e['text']) for e in adventure_entries)
total_choices = sum(len(e['choices']) for e in adventure_entries)
avg_choices = total_choices / len(adventure_entries) if adventure_entries else 0

print("📊 ESTADÍSTICAS DEL LIBRO:")
print(f"  Entradas de aventura: {len(adventure_entries)}")
print(f"  Caracteres totales: {total_text:,}")
print(f"  Promedio por entrada: {total_text/len(adventure_entries):.0f}")
print(f"  Total de choices: {total_choices}")
print(f"  Promedio de choices: {avg_choices:.1f}")
print(f"  Entrada más corta: {min(len(e['text']) for e in adventure_entries)}")
print(f"  Entrada más larga: {max(len(e['text']) for e in adventure_entries)}")

# Entradas sin choices (finales)
no_choices = [e for e in adventure_entries if not e['choices']]
print(f"\n📍 Entradas finales (sin choices): {len(no_choices)}")
for e in no_choices[:5]:
    print(f"   #{e['number']}: {e['text'][:50]}...")
EOF
PYTHON
echo ""

# Notas finales
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ NOTAS IMPORTANTES:"
echo "────────────────────────────────────────────────────────────────────────────────"
echo "1. El protocolo es genérico: funciona con cualquier libro de aventura solitaria"
echo "2. Soporta variantes de formato ('1' y 'B 1')"
echo "3. Genera JSON limpio y clasificado (adventure vs instruction/empty)"
echo "4. Valida automáticamente contra el PDF original"
echo "5. Puede extenderse para análisis adicionales (grafos, ciclos, etc.)"
echo ""
