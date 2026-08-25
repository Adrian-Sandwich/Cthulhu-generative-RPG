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

El backlog original de esta sesión quedó obsoleto: **cinco de sus seis ítems se
cerraron en `52ee13a`** (2026-07-16, "clear the playtest backlog — ES dice,
containment, tutorial, Warner, revolver, moderation") y el documento nunca se
actualizó. Auditado contra el árbol — cada ítem cerrado lleva el ancla que lo
cierra, para no volver a planificar trabajo hecho.

### Cerrado

| ítem original | ancla |
| --- | --- |
| 1. `ROLL_KEYWORDS` bilingüe | `core/keyword_data.py:10` — 107 claves; incluye `investigar`, `revisar`, `leer`, `buscar`, `trepar`, `apuñalar` |
| 2. Contención de mundo + anti-dream-reset | `core/adventure_context.py:175-182` — reglas MOVEMENT ("las locations de la aventura son los ÚNICOS lugares que existen") y CONTINUITY ("el jugador NO puede reescribir la realidad") en el system prompt |
| 4. Warner se presenta temprano | `core/prompts.py:326` (directiva EARLY GAME con `turn <= 3`) + `available_turns: range(1, 10)` en `NPC_DEFINITIONS` |
| 3. Mini-tutorial | `static/app.js:498-503` — 3 líneas bilingües "CÓMO JUGAR / HOW TO PLAY" en el intro, más el tooltip pulsante `#die-tip` ("¡Haz click en el dado!") que se muestra la primera vez que aparece un dado, más la pantalla `[help]` completa (`templates/index.html:115`) |
| 5. Camino al arma | **estuvo mal marcado como cerrado** — la plomería estaba completa pero nada la disparaba. Ver abajo |

### El ítem 5 estuvo mal marcado como cerrado (corregido 2026-08-25)

Lo di por hecho leyendo `core/prompts.py:314` y `pick_up_item`, sin probar si el
modelo dispara el tag. **No lo dispara.** Medido con la telemetría recién
agregada, sobre turnos reales:

- `dm_roll_compliance = 0.0` — el DM pidió 0 de 6 tiradas; las seis las inyectó
  el keyword fallback.
- Capturando la salida cruda: mistral **no emite ningún tag**, de ningún tipo.
- El camino de tool-calling tampoco: mistral, llama3 y neural-chat devuelven
  `tool_calls: []` ante un "take the revolver" inequívoco. Solo `qwen2.5:7b`
  llama `pickup_item` — y no estaba en `TOOL_CAPABLE_MODELS`, mientras que dos
  que no cumplen sí estaban. Lista corregida por medición.

El juego funcionaba igual porque el motor tiene fallback de keywords para
tiradas, combate, cordura y movimiento. **Items y munición eran las dos únicas
mecánicas sin fallback** — exactamente las dos que el playtest reportó ausentes
("0 armas encontradas", "AMMO 6 inútil en todas las partidas"). Verificado antes
del arreglo: parado en Keeper's Quarters, pidiendo el arma de tres formas en dos
idiomas, el inventario quedaba vacío y `ammo` en 0.

Cerrado con `_infer_item_pickup`, mismo patrón que la síntesis de tiradas, con
tres puertas: verbo de tomar **del jugador** (nunca de la prosa del DM — ese es
el error que teletransportaba jugadores con `[LOCATION:]`), sustantivo que mapea
a un item del registro, y ubicación correcta para items que la aventura coloca
(`item_locations` en el config; el revólver vive en Keeper's Quarters). Match por
palabra completa: con substring, "I take the shotgun" concedía el revólver
porque "gun" está dentro de "shotgun".

Sobre el cuchillo de Pao: sigue rechazándose, y eso es correcto — un cuchillo no
está en el registro `ITEMS`. Esa negativa es la contención funcionando.

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

El backlog de julio está cerrado salvo el selector de idioma. Lo que sigue son
huecos encontrados auditando el código, no ítems heredados.

1. **Residuo de descubribilidad del dado** — el tutorial y el tooltip cubren al
   jugador que *ve* el dado, pero no al que pide tirarlo por texto. Champi
   escribió "Lanza el dado" como acción y el Keeper lo recibió como narrativa,
   gastando el turno. Cerrado parcialmente en este branch: el cliente intercepta
   la petición (`ROLL_REQUEST_RE` en `static/app.js`) y explica que los dados
   salen solos. Queda sin cobertura automatizada — el front no tiene tests.
2. ~~**Telemetría por sesión**~~ — **hecho**. Contadores en `GameState.telemetry`
   (persisten en el save), expuestos en `/api/admin/stats` y en el panel DICE
   del dashboard. Lo que se cuenta es solo lo que no queda registrado en otra
   parte — `actions`, `rolls_from_dm`, `rolls_synthesized`, `rolls_thrown`; NPCs,
   inventario y arma se **derivan** del estado para que no puedan desviarse.

   Las dos lecturas que el playtest no podía separar, ahora booleanas por
   sesión: `mechanic_silent` (jugó y nunca se le ofreció un dado → el matcher no
   dispara para cómo escribe) y `dice_undiscovered` (se le ofrecieron dados y no
   tiró ninguno → el dado no es descubrible). Más `dm_roll_compliance`, la
   fracción de tiradas que el DM pidió por sí mismo en vez de que el motor
   tuviera que inyectarla.

   Primera señal de una partida real: el modelo **no** pidió la tirada de
   "trepo por las escaleras" — la sintetizó el motor. Si eso se sostiene, el
   protocolo de tiradas del prompt no se está cumpliendo y el motor lo está
   cargando.
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
