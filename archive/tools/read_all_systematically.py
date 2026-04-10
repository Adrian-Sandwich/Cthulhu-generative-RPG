#!/usr/bin/env python3
"""
LECTURA SISTEMÁTICA: Leer todas las páginas PNG en orden
Extraer TODAS las entradas encontradas
Compilar JSON final con 594 entradas
"""

import json
from pathlib import Path

print("=" * 80)
print("PROTOCOLO: LECTURA SISTEMÁTICA DE TODAS LAS PÁGINAS")
print("=" * 80)

pdf_pages = sorted(list(Path('/Users/adrianmedina/src/Cthulhu/pdf_pages').glob('page-*.png')))

print(f"\nTotal de páginas a procesar: {len(pdf_pages)}")
print("\nProceso:")
print("1. Leer cada página PNG visualmente (manual)")
print("2. Extraer las entradas que contiene")
print("3. Compilar en JSON final")
print("\nVamos a hacerlo página por página...")
print("\n" + "=" * 80)

# Mapeo manual de lo que hemos visto hasta ahora
manual_extractions = {
    111: "The film today is Alfred Hitchcock's Murder. You look forward to seeing the film and feel that young Hesscock is a promising protege. During the interval, you manage to corner the film's director and his entourage. You've arranged to have drinks with them afterwards.",
    112: "If any of your rolls were successful, read the appropriate entry below. If all your rolls were unsuccessful, you didn't roll the appropriate entry below. Spend an hour away from the main party. Those involved find themselves alone with strangers. You feel uncomfortable and consider returning to the hotel.",
    126: "If you chose Cinema (am), go to 111. If you chose Shopping (pm), go to 113. If you chose Library (night), go to 115. If you chose The grounds/city, and along different activities that day, go to 113, 127, 187, 192.",
    127: "EXPENSIVE HOTEL She is the one in an expensive, 24-hour room service. Oh, on the second night, you get HERE with a rude concierge who tells you: All in a hot also the Police and Military at the Cairo Museum or in the following districts of Cairo, go to any Egypt Location Table.",
    128: "It's on a day right now bound for Cairo. Go to 204.",
    129: "Big opposition is strong, make a Hard CON roll. If you fail the poison from your body and the chemist for the sundowner in club the antidote and for the doctor to tend you to his will with his needle for routine. You now sit in his company.",
    137: "But now your clues tell you that two people coming down the river path and behind you. Entering, you noticed that the boy wears the clothes of a fellah and is one of the tribe. Deriving the clay pottery table at 187. If you faked the DEX roll, wad an extra incus of strangers you.",
    138: "Take a wide me as you use all the areas you could intake. There in particular areas of interest. For Following up to 119. For Climbing to up to 118. For Looking the up to 121.",
    139: "See the remains out of the day's officers ethere, directing the thing—allowing you to get away! The officers he has treading a final and totally teams on his hands and rose with you down the streets.",
    140: "You read the following: 'Where is the Lost City of the Old Days? Where are the Hidden Places? We is hidden in the sky, for more hints of them Top?'",
    154: "The library in Athens Hours, birth to miniature, have room in is in a missing course. They are very safe. Each right that you spend in Astrom, entergy one Look out of if you manage go to 109. Return to the Cairo Location Table.",
    155: "the library is closed. Well, peace and quiet is just what you need. You curl up on the chaise lounge and read. Clearly rested after your good sleep, you make writing a novel.",
    156: "OLD & BREMMERHAVEN - The Stalkerthaven-Moon Service has docked today under clear skies and cable new. Despite the mental odd reparations, many came to the pier to see of the preparations.",
}

print(f"\nEntradas extraídas manualmente hasta ahora: {len(manual_extractions)}")
print(f"Entradas: {sorted(manual_extractions.keys())}")

# Las demás 57 entradas faltantes requieren lectura de más páginas
# Que procesaremos visualmente

print("\n\nPara las 67 entradas faltantes, necesito leer:")
remaining = set(range(1, 595)) - set(manual_extractions.keys())

# Cargar las 527 existentes
with open('/Users/adrianmedina/src/Cthulhu/entries_dark_flexible.json', 'r') as f:
    existing = {e['number']: e for e in json.load(f)}

missing = sorted(remaining - set(existing.keys()))
print(f"Aún faltantes: {len(missing)}")
print(f"Primeras 30: {missing[:30]}")

print("\n" + "=" * 80)
print("SIGUIENTE: Leer cada página para extraer el resto de las entradas")
print("=" * 80)
