# Estructura del Proyecto

## Descripción General

El proyecto está organizado en capas lógicas para máxima claridad y mantenibilidad.

### Core (Motores)

**Localización:** `core/`

- `game_universal.py` - Motor universal base que carga cualquier .json
- `game_enhanced.py` - Extiende con journal, save/load, estado
- `game_immersive.py` - Extiende con atmosfera, objetos, imágenes, música

**Cada nivel extiende el anterior, no reemplaza.**

### Games (Interfaces)

**Localización:** `games/`

Diferentes formas de jugar usando el mismo motor:

- `play.py` - CLI simple, minimalista
- `play_improved.py` - CLI mejorada, mejor navegación
- `play_immersive.py` - **PRINCIPAL** - Atmosfera completa
- `play_fixed.py` - Navegación inteligente automática
- `quick_play.py` - Tutorial paso a paso

### Tools (Utilidades)

**Localización:** `tools/`

Herramientas para crear y mantener aventuras:

- `document_to_json.py` - Convierte .txt → .json (el más importante)
- `repair_trace_numbers.py` - Repara referencias rotas
- `fix_all_destinations.py` - Fix masivo de destinos

### Adventures (Aventuras)

**Localización:** `adventures/`

Cada aventura tiene su carpeta con:

```
aventura/
├── AVENTURA.txt              # Archivo de texto plano
├── aventura.json             # JSON (generado automáticamente)
└── aventura.immersive.json   # Datos de atmosfera, objetos, etc
```

**Aventuras disponibles:**

- `point_black/` - Demostración (26 entradas, 6 finales)
- `tide/` - Alone Against the Tide (243 entradas) 
- `dark/` - Alone Against the Dark (594 entradas)
- `examples/` - Ejemplos adicionales

### Docs (Documentación)

**Localización:** `docs/`

- `STORY_FORMAT_SPEC.md` - Especificación completa de formato
- `DOCUMENT_PARSER_GUIDE.md` - Guía del parser
- `IMMERSIVE_ADVENTURE_SYSTEM.md` - Sistema completo
- `STRUCTURE.md` - Este archivo
- Otros `.md` de referencia

### Archivos Media

- `images/` - Imágenes PNG/JPG para aventuras
- `audio/` - Música OGG y SFX WAV

### Archive (Backup)

**Localización:** `archive/`

Archivos viejos, scripts de desarrollo, backup:

- `tools/` - Scripts de prueba/desarrollo
- `data/` - Archivos JSON antiguos
- `pdfs/` - PDFs de referencia
- `misc/` - Otros

---

## Flujo de Datos

```
Tu Historia (texto plano)
    ↓ document_to_json.py
entradas.json (estructura pura)
    + aventura.immersive.json (metadatos)
    ↓ game_immersive.py
Motor cargado
    ↓ play_immersive.py
Interfaz de usuario
    ↓
Experiencia inmersiva del jugador
```

## Cómo Extender

### Agregar Nueva Aventura

1. Crea carpeta en `adventures/mi_aventura/`
2. Escribe `mi_aventura.txt` usando `STORY_FORMAT_SPEC.md`
3. Parsea: `python3 tools/document_to_json.py mi_aventura.txt --output adventures/mi_aventura/mi_aventura.json`
4. Crea `mi_aventura.immersive.json` con atmosfera
5. ¡Listos a jugar!

### Agregar Nueva Interfaz de Juego

1. Copia `games/play_immersive.py`
2. Modifica según necesites
3. Ejecuta: `python3 games/mi_version.py`

### Agregar Capas al Motor

1. Crea archivo en `core/game_xxxx.py`
2. Extiende `game_immersive.py` o la capa anterior
3. Agrega nuevas funcionalidades
4. Usa desde un nuevo juego

---

Esta estructura permite:
- ✅ Colaboración clara
- ✅ Reutilización máxima
- ✅ Fácil mantenimiento
- ✅ Escalabilidad indefinida
