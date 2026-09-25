# Límites del jugador y del narrador

La narración libre recibe la ubicación actual, su descripción, el inventario,
la munición y la última tirada como hechos del servidor. Se pide prosa breve,
detalles sensoriales y opciones abiertas, sin decidir pensamientos del jugador.
Los finales y descubrimientos dependen de las reglas de la aventura.

Antes de mostrar prosa o ejecutar herramientas, se comprueban patrones conocidos
de traslados a otras ubicaciones y recogidas de objetos que el jugador no lleva.
Mencionar un lugar, negar una acción o proponerla condicionalmente sigue permitido.
Esta comprobación complementa las reglas del motor; no comprende toda paráfrasis
posible ni garantiza detectar cualquier contradicción narrativa.

Las acciones son intentos dentro de la ficción. Las peticiones conocidas para
alterar instrucciones, inyectar etiquetas de mecánicas, falsificar dados o reclamar
estadísticas se rechazan con 422 antes de llamar al modelo o crear un turno.
También se comprueban en el motor para los clientes que no usan HTTP. La detección
normaliza caracteres Unicode compatibles y elimina caracteres de formato invisibles.
Engañar a un personaje, ignorar sus susurros o buscar munición siguen permitidos.

El prompt declara que acciones e historia citada no tienen autoridad para cambiar
reglas. La respuesta del narrador se revisa antes de pasar al parser de etiquetas,
las herramientas o SSE. Se rechazan patrones conocidos de razonamiento interno,
mensajes del sistema, identidad de asistente, código y concesiones explícitas de
estadísticas en prosa. Si falla una acción web, se restaura su checkpoint y se
persiste un recibo fallido: no aparecen ni su texto rechazado ni sus recompensas.
Si falla la narración posterior a una tirada ya resuelta, se conserva el resultado
y se utiliza una frase neutral; no se repiten los dados ni sus costes.

La narración se retiene completa antes de mostrarla. SSE sigue transportando el
resultado y los errores, pero el primer texto llega después de validar la respuesta,
con el coste correspondiente en latencia percibida.

Además del prompt, el motor aplica límites independientes:

- El daño declarado por el DM se acumula y limita por turno, tanto para HP como SAN.
  Repetir etiquetas o combinarlas con herramientas no multiplica el límite.
- Objetos y munición proceden de fuentes finitas configuradas por aventura y de
  comandos explícitos; ni etiquetas ni herramientas del DM pueden concederlos.
- Los movimientos requieren conexiones del mapa y sus condiciones de acceso.
  Ver [mapa y recompensas](WORLD_RULES.md).
- Las cantidades en dados tienen límites de longitud, número de dados y caras para
  evitar cálculos descontrolados. Las herramientas mal formadas se descartan.
- Las herramientas procesadas se limitan a 16 por respuesta y sus argumentos se validan.

Estos controles no son un detector semántico completo. Pueden existir paráfrasis
adversarias y falsos positivos; tampoco prueban que toda afirmación narrativa sea
coherente. Los finales narrativos ahora requieren objetivos verificados por tiradas
del servidor y una elección explícita: las etiquetas del DM no tienen autoridad.
Ver [reglas de finales por aventura](ENDING_RULES.md). Mantener casos adversarios y casos de juego legítimo
en `tests/test_guardrails.py` y añadir regresiones cuando aparezca un fallo real.
