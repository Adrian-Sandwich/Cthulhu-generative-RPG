# Finales decididos por el motor

Los finales de historia requieren pruebas persistentes y una elección explícita
del jugador. El DM no puede concederlos con etiquetas, herramientas ni afirmaciones
en la narración. Las etiquetas `ENDING` se rechazan antes de llegar a SSE; incluso
si se omite esa validación, el parser no cambia el final de la partida.

## Point Black

| Final | Tiradas exitosas requeridas | Lugar final | Objeto | Acción explícita de ejemplo |
|---|---|---|---|---|
| Escape | Navigate en el exterior | Exterior | Ninguno | `leave the island` / `abandono la isla` |
| Transformación (`victory`) | Spot Hidden en las habitaciones del farero; Occult en la sala de la linterna; Occult en la cámara oculta | Cámara oculta | Ninguno | `embrace the transformation` / `acepto la transformación` |
| Destrucción | Occult en la sala de la linterna; Occult en la cámara oculta; Investigate en el sótano | Sótano | Dinamita | `detonate the dynamite` / `detono la dinamita` |

Todos estos objetivos aceptan dificultad Normal o superior. Las acciones
`I navigate the coast` y `trazo una ruta` pueden solicitar Navigate mediante el
respaldo del motor aunque el modelo omita la tirada. La dinamita está colocada en
el sótano. Los nombres `victory` y The Ascended conservan el significado anterior
de aceptar la transformación; no se reinterpretan como sellar la fisura.

Las reglas anteriores son decisiones de diseño de esta aventura, no deducciones
del modelo. Las tiradas pueden preceder a la elección final: no se exige una
tirada adicional al confirmar. Ningún final de historia se permite durante combate
activo, con requisitos pendientes o desde otro lugar. La API también exige resolver
primero cualquier tirada pendiente. HP y SAN siguen determinando muerte y locura.

La elección explícita compara la acción completa, normalizando mayúsculas, espacios
y puntuación exterior; no coincide por substrings. Por ejemplo, «no quiero abandonar
la isla» no termina la partida. Las variantes autorizadas están en el config y se
incluyen en las instrucciones del narrador. Si faltan requisitos, la API devuelve
un error y el checkpoint del turno se conserva. Un final autorizado usa narración
preescrita en español/inglés, se guarda con su recibo y no consulta al modelo.

## Añadir otra aventura

`ending_objectives` define identificadores con `location` (clave exacta del mapa),
`skill` (habilidad del motor), `difficulty` y `label`. Sólo `execute_skill_check`
puede registrar un objetivo, tras una tirada exitosa en ese lugar y con dificultad
suficiente. El progreso se deduplica y su tamaño está acotado por los objetivos
definidos; no se deduce de texto, etiquetas ni solicitudes del cliente.

`ending_rules` define escape/victory/destruction con `location`, `requires`
(objetivos obligatorios), `required_items` (claves del inventario), `actions`
(frases explícitas) y `narrative` (texto por idioma, con fallback `en`). Campos
desconocidos, acciones ambiguas, referencias inválidas y finales sin objetivos
se rechazan. Muerte y locura no son finales configurables mediante estas reglas.
Una aventura sin reglas no permite finales concedidos por el narrador.

El progreso se guarda en `game_state.ending_objectives`, tanto en JSON como en
PostgreSQL, sin cambio de esquema SQL. Partidas antiguas empiezan con objetivos
vacíos: no se inventan pruebas a partir de su historia. Se conservan finales ya
guardados; no hay revisión retroactiva de partidas terminadas. Al cambiar el
significado de un objetivo publicado, usar un ID nuevo para no reutilizar pruebas
obtenidas bajo otra condición.

Esto cierra la concesión directa de finales. No demuestra coherencia semántica
completa de la historia: la prosa sigue necesitando controles. La navegación y
las recompensas tienen [reglas propias del motor](WORLD_RULES.md). Las pruebas cubren requisitos, dificultad,
ubicación, combate, guardados antiguos, reinicio, repetición de comandos y progreso
compartido entre servidores PostgreSQL.
