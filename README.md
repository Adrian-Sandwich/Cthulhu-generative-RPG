# ALONE AGAINST THE DARK - Immersive Adventure Engine

## 📁 Estructura de Carpetas

```
cthulhu/
├── core/              # Motores del juego
│   ├── game_universal.py      # Motor base universal
│   ├── game_enhanced.py        # Motor + journal/save
│   └── game_immersive.py       # Motor + inmersión
│
├── games/             # Interfaces de juego
│   ├── play.py                 # Versión simple
│   ├── play_improved.py        # Versión mejorada
│   ├── play_immersive.py       # Versión inmersiva (RECOMENDADO)
│   ├── play_fixed.py           # Versión con smart navigation
│   └── quick_play.py           # Tutorial paso a paso
│
├── tools/             # Herramientas de conversión
│   ├── document_to_json.py     # Convierte .txt → .json
│   ├── repair_trace_numbers.py # Repara referencias
│   └── fix_all_destinations.py # Fix global de destinos
│
├── adventures/        # Aventuras listas para jugar
│   ├── point_black/            # La aventura de demostración
│   │   ├── MINI_ADVENTURE_TEMPLATE.txt
│   │   ├── mini_adventure.json
│   │   └── mini_adventure.immersive.json
│   ├── tide/                   # Alone Against the Tide
│   │   ├── entries_with_rolls.json
│   │   └── investigators.json
│   ├── dark/                   # Alone Against the Dark
│   │   └── entries_dark_594_final.json
│   └── examples/               # Ejemplos
│       ├── example_adventure.txt
│       └── example_entries.json
│
├── docs/              # Documentación completa
│   ├── STORY_FORMAT_SPEC.md            # Cómo escribir aventuras
│   ├── DOCUMENT_PARSER_GUIDE.md        # Guía del parser
│   ├── IMMERSIVE_ADVENTURE_SYSTEM.md   # Sistema completo
│   └── [otros documentos]
│
├── images/            # Imágenes para aventuras
│   └── [tus imágenes aquí]
│
├── audio/             # Música y SFX para aventuras
│   └── [tus audios aquí]
│
└── archive/           # Archivos viejos/backup
    ├── tools/         # Scripts de desarrollo
    ├── data/          # Archivos JSON antiguos
    ├── pdfs/          # PDFs de referencia
    └── misc/          # Otros archivos
```

## 🚀 Quick Start

### 1. Jugar la aventura de demostración

```bash
python3 games/play_immersive.py

# Selecciona: Point Black Lighthouse
# ¡A jugar!
```

### 2. Crear tu propia aventura

```bash
# 1. Lee la especificación
cat docs/STORY_FORMAT_SPEC.md

# 2. Escribe tu aventura
nano mi_aventura.txt

# 3. Convierte a JSON
python3 tools/document_to_json.py mi_aventura.txt --output mi_aventura.json --validate

# 4. Crea datos de inmersión (opcional)
# Copia structure de adventures/point_black/mini_adventure.immersive.json

# 5. Juega
python3 games/play_immersive.py
# Selecciona tu aventura
```

## 📚 Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `core/game_immersive.py` | Motor con atmosfera + objetos + imágenes |
| `games/play_immersive.py` | Interfaz de juego inmersivo |
| `tools/document_to_json.py` | Convierte texto → JSON |
| `docs/STORY_FORMAT_SPEC.md` | Especificación de formato |
| `docs/IMMERSIVE_ADVENTURE_SYSTEM.md` | Guía completa del sistema |

## ✨ Características

- ✅ Aventuras en texto plano (fácil de escribir)
- ✅ Conversión automática a JSON (sin errores)
- ✅ Motor inmersivo (atmosfera, objetos, imágenes)
- ✅ Interfaz intuitiva
- ✅ Soporte para múltiples aventuras
- ✅ Sistema de guardado/carga
- ✅ Mecánicas de D100 (Call of Cthulhu)

## 🎮 Versiones de Juego

| Juego | Características |
|-------|-----------------|
| `play.py` | Simple, minimalista |
| `play_improved.py` | Mejorado, mejor UI |
| `play_immersive.py` | **RECOMENDADO** - Atmósfera, objetos, imágenes |
| `play_fixed.py` | Con smart navigation |
| `quick_play.py` | Tutorial interactivo |

---

**¿Listo? Comienza con `python3 games/play_immersive.py`** 🎭
