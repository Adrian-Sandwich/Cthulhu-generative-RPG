# Sistema de Rolls (Tiradas de Dados)

## ¿Qué pasa cuando llega el momento de tirar dados?

En las aventuras solitarias, cuando el jugador encuentra una instrucción como:
```
• Make a Dodge roll: if you succeed, go to 165; if you fail, go to 144.
```

El sistema debe:

1. **Reconocer** que hay una tirada requerida
2. **Extraer parámetros**: habilidad (Dodge), dificultad (Normal), destinos (165/144)
3. **Mostrar al jugador** lo que necesita hacer
4. **Ejecutar la tirada**: tirar dados + comparar contra habilidad
5. **Navegar** al destino correcto (165 si éxito, 144 si fallo)

## Arquitectura de Rolls

### 1. Extracción de Rolls (en protocolo)

El protocolo de extracción ahora identifica y parsea rolls automáticamente:

```python
# En cada entrada:
{
  "number": 10,
  "text": "Given your recent escape...",
  "choices": [
    "• Make a Fast Talk roll: if you succeed, go to 46; if you fail, go to 101."
  ],
  "rolls": [
    {
      "skill": "Fast Talk",
      "difficulty": "Normal",
      "on_success": 46,
      "on_failure": 101,
      "raw_text": "Make a Fast Talk roll: if you succeed, go to 46; if you fail, go to 101."
    }
  ]
}
```

### 2. Tipos de Rolls Detectados

**Rolls Simples** (la mayoría):
```
Make a Psychology roll: if you succeed, go to 126; if you fail, go to 144.
```

**Rolls con Dificultad**:
```
Make a Hard Dodge roll: if you succeed, go to 165; if you fail, go to 232.
Make an Extreme POW roll: if you succeed, go to 200; if you fail, go to 89.
```

**Rolls Alternativos** (raramente):
```
Make an Appraise or Credit Rating roll: if you succeed, go to 100; if you fail, go to 14.
```

### 3. Habilidades y Características Detectadas

**Habilidades Comunes**:
- Psychology, Dodge, Stealth, Listen, Navigate
- Charm, Persuade, Fast Talk, Appraise
- Fighting (Brawl), Climb, Jump, Spot Hidden
- Locksmith, etc.

**Características (ratings)**:
- STR (Strength), CON (Constitution), DEX (Dexterity)
- POW (Power), APP (Appearance), SIZ (Size)
- INT (Intelligence), EDU (Education)

### 4. Dificultades

El sistema Call of Cthulhu define tres dificultades:

| Dificultad | Modificador | Descripción |
|-----------|-------------|------------|
| **Normal** | ×1 | Dificultad estándar (20% de probabilidad base) |
| **Hard** | ÷2 | Mitad de la probabilidad (10% base) |
| **Extreme** | ÷5 | Un quinto de la probabilidad (4% base) |

## Estadísticas Actuales

De las 243 entradas extraídas:
- **71 entradas** tienen instrucciones de rolls
- **84 rolls totales** detectados
- **19 rolls de Dodge** (la más frecuente)

### Top 10 Skills/Characteristics:
1. Dodge - 19 veces
2. CON (Constitution) - 15 veces
3. DEX (Dexterity) - 13 veces
4. Luck - 9 veces
5. STR (Strength) - 7 veces
6. Navigate - 6 veces
7. Stealth - 5 veces
8. Listen - 4 veces

## Flujo de Ejecución en Tiempo de Juego

```
┌─────────────────────────────────────────────────────┐
│ 1. Mostrar Entrada Normal                           │
│    "You see a locked door..."                       │
│    Choices:                                          │
│    • Go to 23 (Normal path)                         │
│    • Make a Locksmith roll...                       │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 2. Detectar Que Hay un Roll Requerido               │
│    Sistema identifica: RollInfo(                     │
│      skill="Locksmith",                              │
│      difficulty="Normal",                            │
│      on_success=108,                                 │
│      on_failure=75                                   │
│    )                                                 │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 3. Preparar Tirada                                   │
│    Obtener valor de habilidad del investigador:     │
│    investigator.skills['Locksmith'] = 45            │
│    Dificultad = Normal (no modificador)             │
│    Target = 45%                                      │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ 4. Tirar Dados                                       │
│    Opción A: Automático                              │
│      - Generar número aleatorio 1-100               │
│      - Si ≤ 45 → ÉXITO                              │
│      - Si > 45 → FALLO                              │
│                                                      │
│    Opción B: Manual (Jugador especifica resultado)   │
│      - Usuario ingresa "75" (resultado d100)         │
│      - Sistema compara: 75 > 45? FALLO               │
└─────────────────────────────────────────────────────┘
                    ↙           ↘
          ┌──────────────┐   ┌──────────────┐
          │ ÉXITO        │   │ FALLO        │
          │ Resultado ≤  │   │ Resultado >  │
          │ habilidad    │   │ habilidad    │
          └──────────────┘   └──────────────┘
               ↓                  ↓
          ┌──────────────┐   ┌──────────────┐
          │ ir a 108     │   │ ir a 75      │
          │              │   │              │
          └──────────────┘   └──────────────┘
```

## Implementación Requerida

### En el Motor del Juego:

```python
def handle_roll(entry, choice_index, investigator):
    """
    Maneja una tirada de dados.
    
    Args:
        entry: Entrada actual con rolls
        choice_index: Índice del choice (puede tener roll)
        investigator: Datos del investigador
    
    Returns:
        entry_number: A dónde navegar (on_success o on_failure)
    """
    
    # 1. Obtener instrucción de roll
    roll = entry.rolls[choice_index] if choice_index < len(entry.rolls) else None
    if not roll:
        # No hay roll, navegar normalmente
        return entry.choices[choice_index].destination
    
    # 2. Obtener valor de habilidad del investigador
    skill_value = investigator.get_skill(roll.skill)
    
    # 3. Aplicar modificador de dificultad
    target = skill_value
    if roll.difficulty == "Hard":
        target = skill_value // 2
    elif roll.difficulty == "Extreme":
        target = skill_value // 5
    
    # 4. Tirar datos
    d100 = random.randint(1, 100)  # O input del jugador
    
    # 5. Determinar resultado
    if d100 <= target:
        print(f"✓ ÉXITO en {roll.skill} ({d100} ≤ {target})")
        return roll.on_success
    else:
        print(f"✗ FALLO en {roll.skill} ({d100} > {target})")
        return roll.on_failure
```

## Características No Implementadas Aún

- ⚠️ Sistema de características (STR, CON, etc.) completo
- ⚠️ Rolls opuestos (dos personas tirando contra)
- ⚠️ Modificadores circunstanciales
- ⚠️ Pushes de rolls (reintentos)
- ⚠️ Sanity checks (tiradas de cordura)

## Validación Cruzada

El protocolo valida que:
- ✓ Todos los destinos (on_success, on_failure) existen en el libro
- ✓ Los nombres de habilidades son válidos (Call of Cthulhu 7e)
- ✓ Las dificultades son correctas (Normal/Hard/Extreme)

## Ejemplos de Rolls en "Alone Against the Tide"

### Entry 10 - Fast Talk Roll
```
Entry: You weigh your options...
Roll: Fast Talk [Normal]
  Success → Entry 46: "Officer convinced"
  Failure → Entry 101: "Officer suspicious"
```

### Entry 11 - Stealth Roll  
```
Entry: You slip in quietly...
Roll: Stealth [Normal]
  Success → Entry 165: "Nobody notices"
  Failure → Entry 144: "They see you!"
```

### Entry 14 - Charm Roll (Hard)
```
Entry: You approach her...
Roll: Charm [Hard] (target = 50% / 2 = 25%)
  Success → Entry 43: "She's impressed"
  Failure → Entry 57: "Not interested"
```

## Próximos Pasos

1. **Crear generador de investigadores** - Asignar valores a skills/características
2. **Implementar motor de rolls** - Tirar dados, comparar, navegar
3. **Agregar histórico de rolls** - Qué se tiró y cuándo
4. **Sistema de sanity** - Rolls de cordura en eventos horribles
5. **Validación de integridad** - Verificar que todos los rolls apunten a entradas válidas

## Referencias

- Call of Cthulhu 7th Edition Keeper Rulebook
- "Alone Against the Tide" PDF format specification
- Sistema de rolls: Manual de reglas (páginas 65-85)
