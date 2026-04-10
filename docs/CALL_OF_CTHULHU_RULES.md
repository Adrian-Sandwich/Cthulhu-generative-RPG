# Sistema de Rolls - Call of Cthulhu 7ª Edición

## ¿Qué dados se usan?

### Respuesta Corta: **SOLO D100 (Percentil)**

En Call of Cthulhu 7ª edición:
- **Todos los rolls de habilidades/características son D100**
- No hay D20, D12, D6, etc. (excepto para daño)
- Comparas el resultado contra el valor de la habilidad

## Cómo Funciona

### Roll Normal
```
Situación: Intentas trepar una pared
Habilidad: Climb = 45%

1. Tirar d100 (genera número 1-100)
2. Resultado: 67
3. Comparar: 67 > 45? → FALLO

Resultado: No puedes trepar
```

### Roll Hard (Mitad de probabilidad)
```
Situación: Trepar con una sola mano
Habilidad: Climb = 45%, modificado a Hard

1. Tirar d100
2. Resultado: 23
3. Comparar contra: 45 ÷ 2 = 22 (aprox)
4. 23 > 22? → FALLO

Resultado: Casi lo logras, pero no
```

### Roll Extreme (Una quinta parte)
```
Situación: Trepar en completa oscuridad mientras llueve
Habilidad: Climb = 45%, modificado a Extreme

1. Tirar d100
2. Resultado: 08
3. Comparar contra: 45 ÷ 5 = 9 (aprox)
4. 8 ≤ 9? → ÉXITO

Resultado: ¡Lo lograste contra todas las probabilidades!
```

## Tipos de Rolls Según Uso

### 1. Roll Normal (Regular)
- Se usa en situaciones estándar
- Comparar d100 ≤ valor de habilidad
- Probabilidad = valor de habilidad %
- **Ejemplo**: "Make a Psychology roll: if you succeed, go to 126; if you fail, go to 144"

### 2. Roll Hard
- Se usa cuando las circunstancias son desfavorables
- Comparar d100 ≤ (valor de habilidad ÷ 2)
- Probabilidad = (valor de habilidad) % ÷ 2
- **En el libro**: "Make a Hard Dodge roll"

### 3. Roll Extreme  
- Se usa en situaciones casi imposibles
- Comparar d100 ≤ (valor de habilidad ÷ 5)
- Probabilidad = (valor de habilidad) % ÷ 5
- **En el libro**: "Make an Extreme POW roll"

### 4. Roll Opuesto (Opposed Roll)
- Dos personas compiten
- Ambas tiran d100
- Quien saca el número más BAJO gana
- **En el libro**: "Opposed Psychology roll" (NO APARECE en Alone Against the Tide)

### 5. Pushing a Roll
- Si fallas un roll, puedes reintentarlo UNA VEZ
- Pero hay consecuencias (daño mental/físico)
- **En el libro**: "If you fail this roll, you may attempt to push it and roll again, but..." (aparece algunas veces)

## Lo Importante: SIN ESPECIFICACIÓN = D100

El libro **NO especifica "d100" en cada instrucción** porque asume que:
- El jugador ya conoce las reglas de Call of Cthulhu
- En CoC, el roll estándar es SIEMPRE d100
- Si dice "Make a Dodge roll" → automáticamente es d100

## Datos de Daño (Diferente)

Para **daño de armas** SÍ hay variedad de dados:
- Puño: 1d3
- Revólver: 1d8
- Rifle: 2d6
- Escopeta: 2d6 o 4d6 (depende)

**PERO** esto es para resolver el daño DESPUÉS de un roll exitoso, no para el roll mismo.

## En "Alone Against the Tide"

Analizando los 84 rolls del libro:
- **84 rolls** = todos D100
- **0 rolls** de otro tipo
- Variaciones solo en dificultad (Normal/Hard/Extreme)

### Distribución de Dificultades
```
Normal    ███████████████████ ~70 rolls (83%)
Hard      ███ ~10 rolls (12%)
Extreme   ██ ~4 rolls (5%)
```

## Características vs Habilidades

Algunos rolls usan **características** en lugar de habilidades:

**Características (base 10-70)**:
- STR (Strength)
- CON (Constitution)
- DEX (Dexterity)
- APP (Appearance)
- POW (Power)
- SIZ (Size)
- INT (Intelligence)
- EDU (Education)

**Ejemplo de roll con característica**:
```
"Make a DEX roll: if you succeed, go to 165; if you fail, go to 144"
→ Tiras d100, comparas contra DEX del investigador (ej: 55)
```

Pero sigue siendo **D100**.

## Sistema Simplificado para la Aventura

Para "Alone Against the Tide", el flujo es:

```python
def resolve_roll(roll_instruction, investigator):
    """
    Resuelve un roll de manera simple.
    """
    
    # 1. Obtener valor de habilidad/característica
    if roll_instruction.skill in investigator.skills:
        base_value = investigator.skills[roll_instruction.skill]
    else:
        base_value = investigator.characteristics[roll_instruction.skill]
    
    # 2. Aplicar modificador de dificultad
    target_value = base_value
    if roll_instruction.difficulty == "Hard":
        target_value = base_value // 2
    elif roll_instruction.difficulty == "Extreme":
        target_value = base_value // 5
    
    # 3. Tirar D100
    d100_result = roll_d100()  # 1-100
    
    # 4. Comparar
    if d100_result <= target_value:
        return roll_instruction.on_success  # Éxito
    else:
        return roll_instruction.on_failure   # Fallo
```

## Conclusión

✅ **Respuesta a tu pregunta:**

**SÍ, solo necesitas UN tipo de roll: D100**

Las variaciones son:
- **Dificultad** (Normal/Hard/Extreme) - modifica el target, no los dados
- **Opposed** (raramente) - ambos tiran d100, gana quien saca más bajo
- **Pushing** (raramente) - reintentar después de fallar

Pero siempre es **tirar d100 y comparar contra un valor**.

## Para el Código

```python
# El sistema es muy simple:

def roll_check(skill_value, difficulty="Normal"):
    """Resuelve un check de habilidad"""
    
    # Ajustar target por dificultad
    target = skill_value
    if difficulty == "Hard":
        target = target // 2
    elif difficulty == "Extreme":
        target = target // 5
    
    # Tirar d100
    roll = random.randint(1, 100)
    
    # Comparar
    return roll <= target

# Uso:
psychologist_psychology = 65
result = roll_check(psychologist_psychology, difficulty="Normal")
# Si roll ≤ 65: True (éxito)
# Si roll > 65: False (fallo)
```

## Excepciones/Variantes Raras

Algunas entradas pueden tener:
- Rolls opuestos (dos personas)
- Rolls múltiples (tirar varias veces)
- Modificadores situacionales (+10%, -20%, etc.)

Pero en "Alone Against the Tide" no aparecen estas rarezas.
