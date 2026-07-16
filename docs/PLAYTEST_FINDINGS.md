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

## Backlog priorizado (post-feedback)

1. ROLL_KEYWORDS bilingüe (prerequisito para re-habilitar ES)
2. Contención de mundo en prompt + regla anti-dream-reset
3. Mini-tutorial (3 líneas intro + tooltip primer dado)
4. Warner se presenta solo en turnos tempranos
5. Camino claro al arma/revólver (AMMO no debe ser decorativo)
6. Re-habilitar selector de idioma

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
