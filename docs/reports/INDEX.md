# ÍNDICE - Alone Against the Dark

## 📁 Estructura de Carpetas

```
cthulhu/
├── core/                    # 🔧 MOTORES DEL JUEGO
├── games/                   # 🎮 INTERFACES (JUGAR AQUÍ)
├── tools/                   # 🛠️  HERRAMIENTAS (crear aventuras)
├── adventures/              # 📚 AVENTURAS LISTAS PARA JUGAR
├── docs/                    # 📖 DOCUMENTACIÓN
├── images/                  # 🖼️  IMÁGENES (para futuro)
├── audio/                   # 🎵 MÚSICA/SFX (para futuro)
├── archive/                 # 📦 ARCHIVOS VIEJOS
└── README.md                # Este archivo
```

---

## 🎮 CÓMO JUGAR

### ⭐ Opción 0: GENERATIVE EDITION (NUEVO - AI Dungeon Master)

```bash
python3 games/play_generative.py

# Características:
# • AI Dungeon Master (Mistral 7B local)
# • Narrativa dinámica e ilimitada
# • Personajes precargados o crear nuevo
# • Reglas CoC 7e integradas
# • 5 finales posibles
# • Juego completamente abierto
```

**[Ver documentación completa →](GENERATIVE_EDITION.md)**

---

### Opción 1: Aventura de Demostración (Fija)

```bash
python3 games/play_immersive.py

# Selecciona: Point Black Lighthouse
# Disfruta la experiencia inmersiva
```

**Características:**
- 26 entradas narrativas
- 58 decisiones significativas
- 6 finales diferentes
- Atmósfera completa
- 100% funcional

### Opción 2: Aventura Clásica (Tide)

```bash
python3 games/play_immersive.py

# Selecciona: Alone Against the TIDE
# Investigate coastal mysteries
```

**Características:**
- 243 entradas
- Múltiples personajes
- Aventura original de Call of Cthulhu

### Opción 3: Aventura Antártica (Dark)

```bash
python3 games/play_immersive.py

# Selecciona: Alone Against the DARK
# Antarctic expedition horror
```

**Características:**
- 594 entradas
- La más compleja y larga
- Experiencia épica

---

## 🔧 CORE (Motores)

**Localización:** `core/`

| Archivo | Propósito |
|---------|-----------|
| `game_universal.py` | Motor base universal (carga cualquier JSON) |
| `game_enhanced.py` | Extiende con journal, save/load, estado |
| `game_immersive.py` | **ACTUAL** - Atmosfera, objetos, imágenes, música |

**Arquitectura en capas:**
```
game_universal (base)
    ↓ extiende
game_enhanced (persistencia)
    ↓ extiende
game_immersive (inmersión)
```

---

## 🎮 GAMES (Interfaces)

**Localización:** `games/`

| Script | Características | Cuándo usar |
|--------|-----------------|-------------|
| `play.py` | Simple, minimalista | Prototipado rápido |
| `play_improved.py` | Mejorada, mejor UI | Navegación clara |
| `play_immersive.py` | **RECOMENDADO** - Atmosfera, objetos | Experiencia inmersiva |
| `play_fixed.py` | Smart navigation automática | Evitar dead-ends |
| `quick_play.py` | Tutorial paso a paso | Primeros pasos |

**Ejecutar cualquier versión:**
```bash
python3 games/play_immersive.py    # La mejor
```

---

## 🛠️ TOOLS (Herramientas)

**Localización:** `tools/`

### Crear una Aventura Nueva

**Paso 1: Escribir**
```bash
# Lee la especificación
cat docs/STORY_FORMAT_SPEC.md

# Escribe tu aventura en formato simple
nano mi_aventura.txt
```

**Paso 2: Parsear**
```bash
python3 tools/document_to_json.py mi_aventura.txt \
  --output mi_aventura.json \
  --validate
```

**Paso 3: Jugar**
```bash
# Copia a una carpeta en adventures/
mkdir -p adventures/mi_aventura
cp mi_aventura.* adventures/mi_aventura/

# Juega
python3 games/play_immersive.py
```

### Reparar Aventuras Existentes

```bash
# Si las referencias están rotas
python3 tools/repair_trace_numbers.py mi_aventura.json

# Fix global de destinos
python3 tools/fix_all_destinations.py mi_aventura.json
```

---

## 📚 ADVENTURES (Aventuras)

**Localización:** `adventures/`

### Point Black Lighthouse (DEMOSTRACIÓN)

```
adventures/point_black/
├── MINI_ADVENTURE_TEMPLATE.txt        # Código fuente (26 entradas)
├── mini_adventure.json                # Datos parseados
└── mini_adventure.immersive.json      # Atmósfera + objetos
```

**Acceso:**
```bash
python3 games/play_immersive.py
# Selecciona: Point Black Lighthouse
```

### Tide

```
adventures/tide/
├── MINI_ADVENTURE_TEMPLATE.txt        # Código fuente
├── entries_with_rolls.json            # 243 entradas
└── investigators.json                 # 4 personajes
```

**Acceso:**
```bash
python3 games/play_immersive.py
# Selecciona: Alone Against the TIDE
```

### Dark

```
adventures/dark/
├── entries_dark_594_final.json        # 594 entradas
└── [investigators.json - opcional]
```

**Acceso:**
```bash
python3 games/play_immersive.py
# Selecciona: Alone Against the DARK
```

### Examples

```
adventures/examples/
├── example_adventure.txt              # Ejemplo parseado
└── example_entries.json               # JSON generado
```

---

## 📖 DOCS (Documentación)

**Localización:** `docs/`

### Documentos Principales

| Documento | Propósito |
|-----------|-----------|
| `STORY_FORMAT_SPEC.md` | **Cómo escribir aventuras** (lee esto primero) |
| `DOCUMENT_PARSER_GUIDE.md` | Guía detallada del parser |
| `IMMERSIVE_ADVENTURE_SYSTEM.md` | Sistema completo de inmersión |
| `STRUCTURE.md` | Arquitectura técnica del proyecto |
| `README.md` | Quick start |

### Documentos de Referencia

- `CALL_OF_CTHULHU_RULES.md` - Mecánicas de juego
- `DICE_MECHANICS_SUMMARY.md` - Sistema de D100
- `ROLLS_SYSTEM.md` - Cómo funcionan las tiradas
- Y otros más...

---

## 🖼️ IMAGES & 🎵 AUDIO

**Localización:** `images/` y `audio/`

Actualmente vacías. Para agregar inmersión:

1. **Imágenes:**
   ```bash
   # Copia PNG/JPG a images/
   cp tu_imagen.png images/
   
   # Referencia en adventures/mi_aventura/mi_aventura.immersive.json
   "images": {
     "1": {
       "path": "images/tu_imagen.png",
       "caption": "Descripción"
     }
   }
   ```

2. **Audio:**
   ```bash
   # Copia OGG/WAV a audio/
   cp tu_musica.ogg audio/
   
   # Referencia en .immersive.json
   "music": {
     "default": "audio/ambient.ogg",
     "5": "audio/horror.ogg"
   }
   ```

---

## 📦 ARCHIVE (Backup)

**Localización:** `archive/`

Contiene:
- Versiones anteriores de archivos
- Scripts de desarrollo
- Backup de datos
- PDFs de referencia

**No necesitas acceder aquí normalmente.**

---

## 🚀 QUICK START

### Para Jugar Ahora

```bash
python3 games/play_immersive.py
```

Selecciona una aventura y ¡disfruta!

### Para Crear una Aventura

1. Lee: `docs/STORY_FORMAT_SPEC.md`
2. Escribe: `mi_aventura.txt`
3. Parsea: `python3 tools/document_to_json.py mi_aventura.txt --output mi_aventura.json --validate`
4. Juega: `python3 games/play_immersive.py`

### Para Entender la Arquitectura

1. Lee: `docs/STRUCTURE.md`
2. Lee: `docs/IMMERSIVE_ADVENTURE_SYSTEM.md`
3. Explora: `core/` y `games/`

---

## 📊 Resumen

| Elemento | Estado |
|----------|--------|
| **Motor Inmersivo** | ✅ Completo |
| **Aventura Demo** | ✅ 26 entradas, 6 finales |
| **Aventura Tide** | ✅ 243 entradas |
| **Aventura Dark** | ✅ 594 entradas |
| **Parser Texto→JSON** | ✅ Robusto |
| **Documentación** | ✅ Completa |
| **Sistema de Objetos** | ⏳ Implementado, no activado |
| **Soporte de Imágenes** | ⏳ Listo para conectar |
| **Soporte de Música** | ⏳ Listo para conectar |

---

## 💡 Próximos Pasos

1. **Prueba la aventura demo:**
   ```bash
   python3 games/play_immersive.py
   ```

2. **Lee la especificación:**
   ```bash
   cat docs/STORY_FORMAT_SPEC.md
   ```

3. **Crea tu aventura** o **comparte ideas** para que yo cree historias nuevas

4. **Agrega imágenes y música** a tus aventuras

---

## 🎭 Filosofía del Sistema

✅ **Simplicidad** - Texto plano, fácil de escribir
✅ **Robustez** - Parseo automático, sin errores manuales
✅ **Flexibilidad** - Múltiples interfaces, mismo motor
✅ **Escalabilidad** - Funciona para 10 o 1000 entradas
✅ **Extensibilidad** - Capas lógicas, fácil de expandir
✅ **Inmersión** - Atmosfera, objetos, imágenes, música

---

**¿Listo para empezar? ⬇️**

```bash
python3 games/play_immersive.py
```

🎭 **Welcome to Alone Against the Dark** 🎭
