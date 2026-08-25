# Playtest Findings — 2026-07-14 (LAN session)

First multi-player LAN playtest. 4 players over ~2 hours: Lysis Selene,
Pao, Champi, angelin bananin (plus Adrian's own sessions). Sessions served
from one Mac (`HOST=0.0.0.0`, port 5001), per-browser cookie isolation.
All autosaves preserved in `saves/generative/`.

## Direct feedback (Lysis Selene, WhatsApp)

> "Está chulo" · "Veo que le puedo decir cualquier mamada" · "Me da mucha
> libertad de escritura. No le hayo." · "Después de lanzar el dado no le
> supe [cómo avanzo]"

Signals: freedom paralysis (too open, no guidance) and a dead-end after
roll resolution. → Addressed same day with suggested-action chips
(`7465169`). Tutorial pending (see backlog).

## Session mining (from autosaves)

### Pao — 13 turnos, HP 6, SAN 63, español
- 2 climbs fallidos seguidos → abandonó la ruta (frustración temprana).
- Usó "rezo" (mecánica de descanso funcionó).
- **"agarro un cuchillo"** — el DM se lo concedió de palabra; inventario
  real: vacío. Items narrativos ≠ items mecánicos.
- **"me entierro el cuchillo y me muero"** → no pasó nada mecánico →
  **se reescribió la realidad**: "desperté del sueño... me tiene
  secuestrada el asesino". El DM siguió la nueva historia (secuestro/
  crimen). Autoridad narrativa no cubre resets tipo "era un sueño".

### Champi — 12 turnos, SAN 79, mezcló EN/ES
- Se auto-narra en 3ª persona ("Champi tiene una idea...") y el DM obedece.
- El DM le inventó una **cueva con flores** dentro del faro (deriva de canon).
- Escribió **"Lanza el dado" como acción de texto** — no supo que el dado
  se clickea. Señal fuerte de tutorial.
- 1 tirada en 12 turnos.

### angelin bananin — 30 turnos, SAN 36, español
- Jugó un **detective procedural completo fuera del mapa**: comisaría,
  biblioteca, laboratorio de análisis de agua, "líder del equipo de
  investigación". Nada de eso existe en la aventura; el DM lo compró todo.
- **0 tiradas en 29 acciones.** Verbos en español ("investigar", "revisar",
  "leer") no están en ROLL_KEYWORDS → sin síntesis de dados.
- SAN sí bajó (36) — los triggers de horror funcionaron.

### Transversal (los 3)
- **0 NPCs conocidos** — Warner/Armitage nunca aparecen si el jugador no
  los invoca. Contenido invisible.
- **0 armas encontradas** — AMMO 6 inútil en todas las partidas.
- Nadie llegó a un ending.

## Hallazgos estructurales (orden de gravedad)

1. **ROLL_KEYWORDS es inglés-only** → jugadores en español casi no tiran
   dados → el juego degrada a "ChatGPT con interfaz". El gap más grave.
2. **Contención de mundo débil** — la autoridad narrativa bloquea lo
   flagrante (crossover/kamehameha) pero no la deriva plausible
   (biblioteca del pueblo, comisaría, cueva). Falta regla: la isla del
   faro ES todo el mapa; el DM redirige la deriva.
3. **Resets narrativos** — "muero... era un sueño" reescribe la realidad.
   Falta: muerte/daño narrado por el jugador = consecuencia mecánica; sin
   dream-resets.
4. **NPCs nunca presentados** — el DM debe introducir a Warner en los
   primeros turnos (su definición dice turnos 1-10 y jamás sucede).
5. **Onboarding** — confirmar con chips + mini-tutorial (3 líneas +
   tooltip de primera tirada).

## Decisiones tomadas

- **2026-07-15: Español PAUSADO** (selector oculto, server fuerza `en`)
  hasta cerrar #1 y #2. La infraestructura i18n queda intacta
  (`language` param, `story_seed_i18n`, directivas) — re-habilitar es
  quitar el gate.
- Chips de sugerencias ya enviados (`7465169`).
- **2026-08-25: la condición del gate de español se cumplió** — #1 y #2
  están cerrados (ver Backlog auditado). Lo único que queda para
  re-habilitarlo es quitar el forzado de `app.py:294`.

## Backlog auditado (2026-08-25)

El backlog original de esta sesión quedó obsoleto: cuatro de sus seis ítems ya
están en el código. Auditado contra el árbol en `d692d52` — cada ítem cerrado
lleva el ancla que lo cierra, para no volver a planificar trabajo hecho.

### Cerrado

| ítem original | ancla |
| --- | --- |
| 1. `ROLL_KEYWORDS` bilingüe | `core/keyword_data.py:10` — 107 claves; incluye `investigar`, `revisar`, `leer`, `buscar`, `trepar`, `apuñalar` |
| 2. Contención de mundo + anti-dream-reset | `core/adventure_context.py:175-182` — reglas MOVEMENT ("las locations de la aventura son los ÚNICOS lugares que existen") y CONTINUITY ("el jugador NO puede reescribir la realidad") en el system prompt |
| 4. Warner se presenta temprano | `core/prompts.py:326` (directiva EARLY GAME con `turn <= 3`) + `available_turns: range(1, 10)` en `NPC_DEFINITIONS` |
| 5. Camino al arma | `core/prompts.py:314` siembra el .38 en Keeper's Quarters con instrucción explícita de emitir `[ITEM_FOUND: revolver]`; `pick_up_item` (`core/game_generative.py:957`) carga la munición de la aventura al recogerlo |

Sobre el cuchillo de Pao ("agarro un cuchillo" concedido de palabra, inventario
vacío): el pipeline de items está completo y validado — `[ITEM_FOUND: key]` →
`apply_turn_consequences` (`core/game_generative.py:1472`) → `pick_up_item` →
valida contra el registro `ITEMS` (`core/game_generative.py:80`, 8 items). Un
cuchillo no está en el registro, así que hoy se rechaza por diseño. No falta
protocolo; lo que falló fue narración sin tag.

### Regresión encontrada y corregida durante la auditoría

`[LOCATION: <name>]` — el tag que arregló las locations rotas en español — se
había quedado sin resolvedor. La extracción de módulos de `d692d52` borró
`_resolve_location` y dejó vivo su call site en `core/game_generative.py:737`,
así que **cada movimiento etiquetado por el DM devolvía HTTP 500** y el jugador
perdía el turno. Pasó los tests porque la fixture de `tests/test_smoke.py`
prometía "tag-rich response" y devolvía prosa sin un solo tag.

Cerrado con: `AdventureConfig.resolve_location()` (el módulo dueño del registro
de locations), wrapper delegante en el engine, y cobertura de las 9 etiquetas de
`core/tag_parser.py` en un solo test para que un call site huérfano en cualquier
ruta de tags falle en CI en vez de llegar al jugador.

### Abierto, en orden

1. **Mini-tutorial** (descubribilidad del dado) — único ítem del backlog
   original que sigue vivo, y el mejor respaldado por los datos: Champi escribió
   "Lanza el dado" como acción de texto y Lysis dijo "después de lanzar el dado
   no le supe [cómo avanzo]". Dos testers independientes, sin lectura causal
   alternativa.
2. **Telemetría por sesión** — contadores de tiradas intentadas vs. parseadas,
   NPCs encontrados, arma adquirida, ending alcanzado, turnos. Con n=4 no se
   puede distinguir "mecánica inalcanzable" de "mecánica no señalizada"; esto lo
   dirime y convierte cada partida futura en muestra, sin depender de organizar
   otra sesión LAN.
3. **Re-habilitar selector de idioma** — `app.py:294` fuerza `language = 'en'`.
   La infraestructura i18n está intacta, así que es quitar el gate y des-ocultar
   el selector; sin endpoints nuevos.
4. **Blueprints en `app.py`** — `create_app` tiene complejidad ciclomática 115 y
   cognitiva 224: **763 de 810 líneas del archivo viven dentro de esa función**,
   con los 16 endpoints como closures anidados (el grafo de código detecta 0
   nodos Route de Flask). Partición por dependencia de estado: `game_bp` 9,
   `admin_bp` 2 (`/admin`, `/api/admin/stats`), `api_bp` 3 (`/api/archetypes`,
   `/api/feedback`, `/api/health`), y `/` + `/images/<path>` se quedan. La razón
   no es estética: hoy ningún endpoint es importable, así que toda la cobertura
   HTTP depende de una fixture que instancia la app entera — el hueco exacto por
   el que pasó la regresión de arriba.
5. **Partir `static/app.js`** — cluster único de 53 funciones, cohesión 0.98.
   Cuando el front se toque en serio (ítems 1 y 3).

No hacer: adelgazar el facade de `GenerativeGameEngine`. Los wrappers
delegantes hacia `CombatSystem` / `PromptBuilder` / `CoC7eRulesEngine` son API
estable para los tests y `games/play_generative.py`; quitarlos es churn sin
beneficio medible mientras `app.py` esté como está.


## Feedback de Pao (2026-07-15)

> "los lugares no eran correctos" · "no respetaba los lugares de la isla a
> los que quería cambiar, te deja en el mismo lugar o te mandaba a otro" ·
> "a veces te ponía 'respondiendo a...'" · "hay palabras que siguen en
> inglés cuando cambias de idioma"

Diagnóstico y estado:
1-2. **Locations rotas en español**: `location_keywords` era inglés-only
   ("stairs", "basement") — "voy hacia las escaleras" jamás matcheaba →
   te quedabas o saltabas mal. **Arreglado de raíz**: nuevo tag
   `[LOCATION: <nombre>]` que el DM emite al moverte, **validado contra el
   registro de la aventura** — independiente de idioma, y además rechaza
   lugares inventados (bonus de contención: "Biblioteca del Pueblo" ya no
   existe aunque el DM lo narre). Keywords quedan como fallback.
3. **"Respondiendo a..."**: preámbulo-meta del modelo. **Arreglado**:
   patrón de limpieza EN+ES lo elimina de la salida.
4. **Palabras en inglés mezcladas**: limitación de mistral en ES. Queda en
   el backlog de re-habilitar español (mejor modelo o directiva más dura).

## Pendiente de feedback

- Más sesiones / comentarios de los demás testers.
