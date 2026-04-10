# Respuesta: ¿Qué pasa cuando llega el momento de tirar dados?

## TL;DR

Cuando el juego encuentra una instrucción como:
```
• Make a Dodge roll: if you succeed, go to 165; if you fail, go to 144.
```

El sistema debe:

1. **Identificar** que es un roll (habilidad: Dodge, destino éxito: 165, destino fallo: 144)
2. **Obtener** el valor de Dodge del investigador del jugador
3. **Tirar** un d100 (dados de 1-100)
4. **Comparar**: si d100 ≤ Dodge → éxito (ir a 165), si > → fallo (ir a 144)

## Estado Actual

✅ **Implementado**:
- Parser de instrucciones de rolls
- Extracción automática de rolls de entradas
- Clasificación de dificultades (Normal/Hard/Extreme)
- Análisis de 84 rolls en el libro

⚠️ **Por Hacer**:
- Motor de ejecución de rolls en tiempo de juego
- Sistema de características del investigador
- Validación de integridad (¿existen todos los destinos?)

## Estructura de Datos

Cada entry ahora incluye rolls parseados:

```json
{
  "number": 10,
  "text": "Given your recent escape, you weigh your options...",
  "choices": [
    "• Make a Fast Talk roll: if you succeed, go to 46; if you fail, go to 101.",
    "• To investigate, go to 147."
  ],
  "rolls": [
    {
      "skill": "Fast Talk",
      "difficulty": "Normal",
      "on_success": 46,
      "on_failure": 101
    }
  ]
}
```

## Flujo de Ejecución

```
Jugador selecciona choice con roll
         ↓
Sistema detecta "Make a Fast Talk roll"
         ↓
Extrae parámetros: skill=Fast Talk, target=entry 46, fail=entry 101
         ↓
Obtiene investigador.skills['Fast Talk'] = 45%
         ↓
Tira d100 (resultado: 73)
         ↓
Compara: 73 > 45% → FALLO
         ↓
Navega a Entry 101 (fallo)
```

## Métricas del Libro

- **243 entradas totales**
- **71 entradas con rolls** (29%)
- **84 rolls únicos**

Top 5 Habilidades Más Usadas:
1. Dodge (19 veces) - Esquivar peligro
2. CON (15 veces) - Resistencia física
3. DEX (13 veces) - Destreza
4. Luck (9 veces) - Suerte especial
5. STR (7 veces) - Fuerza

## Lo Que Hace Especial Este Sistema

1. **Genérico** - Funciona con cualquier libro de aventura solitaria
2. **Autoextraído** - Sin código manual, todo desde el PDF
3. **Validable** - Los rolls se pueden verificar contra el PDF original
4. **Extensible** - Fácil agregar más lógica de rolls

## Archivos Generados

- `entries_with_rolls.json` - 243 entradas con rolls parseados
- `ROLLS_SYSTEM.md` - Especificación completa del sistema
- `roll_parser.py` - Parser reutilizable de rolls

## Próximo Paso

Crear el **motor de ejecución de rolls** que:
1. Lee `entries_with_rolls.json`
2. Obtiene datos del investigador
3. Ejecuta tiradas cuando es necesario
4. Navega automáticamente al destino correcto

¿Quieres que implemente el motor de rolls?
