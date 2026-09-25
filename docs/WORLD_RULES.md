# Mapa y recompensas controlados por el motor

## Inventario, pistas y ritmo

La ficha `[inventory & clues]` muestra inventario, munición, hallazgos confirmados
y acciones disponibles en el lugar actual. Escribir `inventory` o `inventario`
abre la ficha sin consumir un turno. También se puede consultar durante una
tirada pendiente mediante el menú; sus botones de acción quedan deshabilitados.
La API acepta esas consultas sin resolver ni reemplazar la tirada pendiente.

`investigations` vincula cada objetivo a `actions` (comandos completos) y `finding`
(texto por idioma, con fallback `en`). Las acciones explícitas usan la habilidad
y dificultad del objetivo, sin pedir permiso al modelo. En Point Black son Normal.
Ejemplos: `search for the keeper key`, `survey the foundations`,
`study the beacon symbols` y `study the fissure`.

Una tirada exitosa registra el objetivo y muestra su texto confirmado, sin
conceder automáticamente objetos. Un fallo conserva el coste del motor y explica
que no se desbloqueó nada; no consulta al modelo para inventar el resultado.
Reconsultar una investigación resuelta no consume turno. La ficha sólo muestra
objetivos obtenidos, nunca el diario completo de una partida futura.

Las partidas nuevas tienen 40 turnos antes de la presión adicional. Los guardados
existentes conservan su reloj, inventario y objetivos. Los recorridos directos
de transformación y destrucción necesitan 23 y 20 acciones respectivamente;
el margen adicional permite fallos y exploración, pero no garantiza ganar.

La recarga del navegador restaura la partida asociada a su cookie, incluida una
tirada pendiente y los hallazgos guardados. No hace falta iniciar otra partida.

El jugador elige una acción explícita; el servidor comprueba el lugar, los
requisitos y el estado de combate antes de modificar la partida. El modelo no
autoriza desplazamientos ni recompensas. Cada movimiento o recogida válido
consume un turno, incluidos los costes del límite de tiempo de la aventura.

## Point Black

El recorrido principal conecta exterior, interior, planta baja y sótano. Desde
el interior se accede a las escaleras, el nivel superior y sus dos habitaciones.
Las habitaciones del farero conectan con el exterior; la cámara oculta, con el
sótano. No se permite saltar habitaciones ni crear destinos mediante texto.

Para entrar a las habitaciones del farero hace falta su llave: se descubre con
Spot Hidden exitoso en el exterior y se recoge explícitamente. La cámara oculta
requiere Investigate exitoso en el sótano y Occult exitoso en la sala de la
linterna. Los objetivos proceden de dados resueltos por el servidor.

Ejemplos: `go to interior`, `voy al interior`, `bajo al sótano`,
`take keeper key`, `tomo la llave`, `take flashlight`. Se compara la acción
completa, normalizando acentos, mayúsculas y espacios. Una acción compuesta no
autoriza varios movimientos. La interfaz recibe sugerencias válidas del servidor.

| Fuente | Lugar | Requisito adicional |
|---|---|---|
| Linterna | Exterior | Ninguno |
| Llave del farero | Exterior | Spot Hidden |
| Cuaderno y revólver | Habitaciones del farero | Ninguno |
| Agua bendita y reserva de 6 balas | Habitaciones del farero | Spot Hidden allí |
| Cuerda | Planta baja | Ninguno |
| Diario | Habitación superior del farero | Evidencia de las habitaciones del farero |
| Texto antiguo | Sala de la linterna | Occult allí |
| Dinamita | Sótano | Investigate allí |

Cada fuente se cobra una vez por partida. Soltar un objeto, gastar sus balas,
cambiar el ID de acción o recargar no restablece la fuente. La reserva de munición
exige espacio para la cantidad completa; un intento sin capacidad no la consume.

## Configurar una aventura

`passages` contiene conexiones dirigidas con `from`, `to`, `requires` (IDs de
objetivos) e `items` (claves de objetos). Cada sentido se declara por separado.
Las ubicaciones admiten `aliases` para comandos en otros idiomas.

`rewards` asigna un ID estable a cada fuente: `location`, `type` (`item` o `ammo`),
`value`, `requires` y `aliases`. Un objeto tiene una sola fuente; los alias no
pueden ser ambiguos dentro del mismo lugar. Se rechazan conexiones duplicadas,
referencias inválidas y cantidades fuera de rango. Sin reglas configuradas no
se conceden movimientos ni recompensas desde el narrador. Al cambiar el
significado de una fuente publicada, usar un ID nuevo.

`game_state.claimed_rewards` persiste en JSON y PostgreSQL. El bloqueo de sesión
y el recibo de acción protegen las peticiones simultáneas y los reintentos. Un
fallo al guardar restaura el checkpoint; repetir un ID devuelve su recibo sin
volver a ejecutar la acción.

En partidas antiguas se conservan ubicación e inventario y se marcan como
cobradas las fuentes de los objetos que el jugador todavía posee. No es posible
reconstruir objetos descartados o munición gastada sin un historial de cobros;
las demás fuentes nuevas empiezan disponibles según sus requisitos. No se
inventan objetivos ni se reubica retroactivamente al jugador.

## Límite del narrador y pruebas

Las etiquetas `LOCATION`, `ITEM_FOUND` y `AMMO_FOUND` se rechazan antes de mostrar
la respuesta, incluido SSE. La herramienta `pickup_item` no se ofrece al modelo;
si este la devuelve de todos modos, se rechaza su propuesta. La prosa libre no
modifica esas mecánicas, aunque estos controles no garantizan detectar toda
afirmación incoherente escrita sin etiquetas.

`tests/test_world_rules.py` cubre recorridos, puertas, combate, fuentes finitas,
reinicios, partidas antiguas, propuestas del modelo, datos falsificados y fallos
al guardar. `tests/test_postgres.py` incluye dos servidores compitiendo por la
misma recompensa con IDs distintos. Ver también [guardarraíles](DM_GUARDRAILS.md)
y [finales](ENDING_RULES.md).
