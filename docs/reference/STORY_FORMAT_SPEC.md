# FORMATO DE DOCUMENTO PARA AVENTURAS CTHULHU

## ESTRUCTURA DEL DOCUMENTO

```
[ENTRY 001]
[TYPE: adventure]
[TITLE: El Comienzo]
[TAGS: investigation, outdoor]

Tu texto de la aventura aquí. Puede ser largo, 
varias líneas, múltiples párrafos. Todo lo que quieras.

Decisiones:
→ Si haces X, go to 012
→ Si haces Y, go to 034

---

[ENTRY 012]
[TYPE: combat]
[TITLE: Encuentro Hostil]
[ROLL: attack/difficult]
[SANITY: -5]

Descripción del combate...

Resultados:
→ Si ganas, go to 045
→ Si pierdes, go to 089
→ Si huyes, go to 012

---
```

## ELEMENTOS OPCIONALES (en el header de cada entry)

| Elemento | Formato | Ejemplo | Uso |
|----------|---------|---------|-----|
| **TIPO** | `[TYPE: ...]` | `adventure`, `combat`, `choice`, `investigation`, `encounter` | Categoría de la entrada |
| **TÍTULO** | `[TITLE: ...]` | `[TITLE: El Misterio del Faro]` | Nombre de la escena |
| **TIRADA** | `[ROLL: skill/difficulty]` | `[ROLL: library/normal]` o `[ROLL: dodge/hard]` | D100 check automático |
| **SANIDAD** | `[SANITY: ±N]` | `[SANITY: -10]` | Daño o recuperación de SAN |
| **PUNTOS DE VIDA** | `[HP: ±N]` | `[HP: -6]` | Daño físico |
| **TAGS** | `[TAGS: ...]` | `[TAGS: investigation, clue, npc]` | Categorías para búsqueda |

## REGLAS DE SINTAXIS

### 1. **Estructura básica de entrada**
```
[ENTRY NNN]
[TYPE: tipo]
[TITLE: nombre]
[OTROS METADATOS]

Texto de la aventura aquí.
Puede ser párrafos múltiples.

Ramificaciones y decisiones:
→ Opción 1: go to NNN
→ Opción 2: go to MMM
```

### 2. **Decisiones/Ramificaciones**
- **Formato:** `→ Descripción, go to NNN` o simplemente `→ go to NNN`
- **Múltiples destinos:** Cada una en línea separada
- **Puntos múltiples:** Si una decisión lleva a múltiples entradas (branch point), listarlas todas
- **Destino por defecto:** `→ Continue to NNN` o `→ default: NNN`

### 3. **Notas especiales en el texto**
- `[CLUE]` - Información importante para investigación
- `[CHOICE]` - Decisión crítica del jugador
- `[CONSEQUENCE]` - Lo que ocurre si el jugador no elige bien
- `[NPC: nombre]` - Introducción de personaje no jugador

### 4. **Separadores**
- `---` entre entradas
- Líneas en blanco para párrafos dentro de una entrada
- Sección de decisiones marcada con `:` al final

## EJEMPLO COMPLETO

```
[ENTRY 001]
[TYPE: adventure]
[TITLE: Llegada a Esbury]
[TAGS: investigation, start]

El ferry se acerca lentamente al muelle de Esbury. 
La tarde cae sobre el lago, y la neblina comienza a cerrarse.

Un marinero robusto y sonriente te saluda al bajar:
[NPC: Lance Sanford] "Bienvenido a Esbury, amigo. Primera vez aquí?"

[CLUE] Notas que hay varios hombres de traje vigilando 
el muelle. Algo raro está pasando.

Decidiste:
→ Hablar con Lance Sanford, go to 004
→ Ir directo a la venta de finca, go to 015
→ Buscar alojamiento, go to 026

---

[ENTRY 004]
[TYPE: encounter]
[TITLE: Conversación con el Marinero]
[TAGS: investigation, clue, npc]

Lance te invita a un café. Mientras toman, te habla 
sobre la muerte del Profesor Harris.

"Murió hace tres días. Fue raro... quedó atrapado 
en el campanario de la iglesia. [CLUE] Nadie sabe 
exactamente qué pasó allá arriba."

→ Preguntar sobre la venta de finca, go to 012
→ Preguntar sobre el Profesor Harris, go to 017
→ Ir directamente a investigar la iglesia, go to 034

---

[ENTRY 012]
[TYPE: investigation]
[TITLE: La Venta de Finca]
[ROLL: library/normal]
[TAGS: investigation, items, auction]

Lance te lleva a la subasta. Es una venta masiva 
de objetos antiguos del Profesor Harris.

[CLUE] Ves varios compradores extranjeros inspeccionando 
ídolos y artefactos antiguos. Algunos parecen muy valiosos.

Si pasas la tirada de investigación:
→ Descubres un vendedor sospechoso, go to 045
→ Encuentras documentos ocultos, go to 089

Si fallas la tirada:
→ Te pierdes en la multitud, go to 026

→ Regresar con Lance, go to 004

---

[ENTRY 017]
[TYPE: choice]
[TITLE: Revelaciones sobre Harris]
[SANITY: -3]

Lance se pone serio. "El Profesor Harris... era un hombre 
peligroso, si me preguntas. Encontró algo en esas expediciones 
a la Antártida. Algo que lo volvió loco."

[CLUE] El marinero menciona "libros antiguos" 
y "símbolos extraños" que el Profesor traía.

→ Presionar para más detalles, go to 087
→ Creer que es superstición, go to 026
→ Ir a buscar los libros de Harris, go to 156

---
```

## ESTRUCTURA DEL ÁRBOL (GENERADO AUTOMÁTICAMENTE)

Cuando proceses el documento, genera un JSON así:

```json
{
  "entries": [
    {
      "number": 1,
      "title": "Llegada a Esbury",
      "type": "adventure",
      "text": "El ferry se acerca lentamente...",
      "tags": ["investigation", "start"],
      "trace_numbers": [4, 15, 26],
      "choices": [
        "Hablar con Lance Sanford, go to 004",
        "Ir directo a la venta de finca, go to 015",
        "Buscar alojamiento, go to 026"
      ],
      "metadata": {
        "sanity_mod": 0,
        "hp_mod": 0,
        "roll": null,
        "clues": 1,
        "npc": ["Lance Sanford"]
      }
    },
    {
      "number": 4,
      "title": "Conversación con el Marinero",
      "type": "encounter",
      "text": "Lance te invita a un café...",
      "tags": ["investigation", "clue", "npc"],
      "trace_numbers": [1, 12, 17, 34],
      "choices": [
        "Preguntar sobre la venta de finca, go to 012",
        "Preguntar sobre el Profesor Harris, go to 017",
        "Ir directamente a investigar la iglesia, go to 034"
      ],
      "metadata": {
        "sanity_mod": 0,
        "hp_mod": 0,
        "roll": null,
        "clues": 1,
        "npc": ["Lance Sanford"]
      }
    }
  ],
  "graph": {
    "1": [4, 15, 26],
    "4": [12, 17, 34],
    "12": [45, 89, 26, 4],
    ...
  },
  "clues": [
    {"entry": 1, "text": "Notas que hay varios..."},
    {"entry": 4, "text": "Nadie sabe exactamente..."},
    ...
  ],
  "npcs": {
    "Lance Sanford": [1, 4],
    ...
  }
}
```

## CONVENCIONES

### Numerar entradas
- **Tide (243 entradas):** 001-243
- **Dark (594 entradas):** 001-594
- Usar 3 dígitos con ceros a la izquierda: `[ENTRY 001]` no `[ENTRY 1]`

### Destinos válidos
- Todos los números deben existir en el documento
- Si un destino no existe, el parser genera advertencia
- `trace_numbers` se genera automáticamente de todos los destinos mencionados

### Tipos de entrada
```
adventure   - Narración sin decisión inmediata
choice      - Decisión importante del jugador
combat      - Encuentro de combate
encounter   - Encuentro con NPC
investigation - Tirada de investigación
puzzle      - Acertijo o desafío
ending      - Conclusión de la aventura
```

### Dificultades de tirada
```
normal     - Tirada estándar (50% base)
hard       - Multiplicar por ½ (25% base)
extreme    - Multiplicar por ¼ (12.5% base)
```

## VENTAJAS DE ESTE FORMATO

✓ **Legible:** Humanos pueden leer y editar fácilmente
✓ **Parseable:** Regex simple puede extraer todo
✓ **Flexible:** Metadatos opcionales, texto libre
✓ **Completo:** Captura todas las mecánicas de Cthulhu
✓ **Validable:** Parser verifica referencias circulares y destinos inválidos
✓ **Versionable:** Texto plano = git-friendly

## SCRIPT PARSER

Crearé `document_to_json.py` que:

1. Lee documento `.txt`
2. Valida estructura
3. Extrae todas las entradas
4. Genera `trace_numbers` automáticamente
5. Verifica que todos los destinos existan
6. Crea archivo `.json` listo para juego
7. Reporta advertencias/errores

```bash
python3 document_to_json.py adventure.txt > entries.json
```

---

**¿Listos? Creamos el parser y probamos con un documento de ejemplo?**
