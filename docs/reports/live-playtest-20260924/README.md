# Auditoría de rutas — 24 de septiembre de 2026

Modelo real: Ollama `qwen2.5:3b`, ejecutado en CPU (`size_vram: 0`), contexto
cargado de 4096 tokens. Académico, dados reales, máximo tres intentos por objetivo.
Recorridos guiados mediante el cliente HTTP de Flask, con guardados aislados.
No se forzaron tiradas ni se inyectaron objetos o pruebas de progreso.

Evidencia: [transcripción completa](transcript.json). Reproducción:
[LIVE_PLAYTEST.md](../../LIVE_PLAYTEST.md).

## Resultado

| Ruta | Resultado | Estado al terminar |
|---|---|---|
| Escape | Completada | Turno 4; Navigate falló con 90 y acertó con 23, objetivo 80 |
| Transformación | Bloqueada por presupuesto de intentos | Turno 20, linterna; Occult 80, 75 y 38 contra 25 |
| Destrucción | Bloqueada por presupuesto de intentos | Turno 14, linterna; Occult 67, 58 y 61 contra 25; dinamita obtenida |

52 peticiones, todas HTTP 200, cero fallbacks en esta ejecución corregida.
La petición más lenta tardó 69,17 segundos. HTTP 200 no implica éxito de los dados
ni coherencia de la narración. Las dos rutas bloqueadas no quedaron validadas
hasta su final; esto tampoco demuestra que sean imposibles.

## Hallazgos y prioridad

1. **Configuración local, corregida.** El constructor del motor imponía `mistral`
   aunque `LLM_MODEL` indicara otro modelo en modo Ollama. La primera ejecución
   recibió 404 y avanzó con fallbacks; se interrumpió y no se contó como prueba
   del narrador. Ahora se respeta el entorno cuando no hay un argumento explícito.
   Una regresión verifica ambos casos. El modo de API alojada conserva su contrato.
2. **Los hallazgos obligatorios necesitan texto confirmado por el motor.** El
   éxito que desbloqueó la llave describió unas iniciales y un personaje inventado,
   sin explicar dónde estaba la llave. El siguiente comando pudo recogerla porque
   el guion conocía la regla. Un jugador sin ese conocimiento podría atascarse.
   Prioridad: presentar el hallazgo autorizado y la acción disponible por separado
   de la descripción libre del DM.
3. **La prosa contradice el estado.** En el exterior se narraron ventana, habitación
   y paredes. Tras Navigate se habló de llegar a mar abierto antes de elegir salir.
   Una investigación fallida describió una trampilla y un pasaje nuevo. El servidor
   no cambió la ubicación ni concedió ese acceso, pero el texto puede confundir.
   Prioridad: dar al narrador un resultado concreto y comprobar afirmaciones sobre
   desplazamientos y descubrimientos, también en las consecuencias de las tiradas.
4. **Dificultad de pistas críticas.** El respaldo por palabras clave convierte
   `search` e `interpret` en dificultad Hard: 22% y 25% con este académico. Ambos
   caminos largos se detuvieron en el segundo tipo. Revisar pistas garantizadas
   con costes o alternativas, y reservar los fallos duros para beneficios opcionales.
   Una ejecución por ruta no basta para estimar tasas de finalización.
5. **Reloj frente al recorrido.** El recorrido directo requiere 23 acciones para
   transformación y 20 para destrucción aun con todas las tiradas exitosas, sin
   exploración adicional. Se empieza en turno 1 y la presión llega después del 18.
   Revisar el presupuesto o el coste de los desplazamientos; actualmente las dos
   rutas largas sufren presión por diseño incluso sin equivocarse.
6. **Latencia y representatividad.** Este modelo pequeño en CPU tardó decenas de
   segundos por narración. Repetir con el proveedor/modelo de producción antes de
   extrapolar calidad o rendimiento. Esta ejecución no prueba navegador, SSE,
   carga concurrente ni facilidad de descubrir las rutas sin conocerlas.

## Validación de cambios

- 298 pruebas pasan, incluidas PostgreSQL y frontend.
- Pyright: cero errores y advertencias en los dos archivos Python modificados
  para esta auditoría; el config sigue avisando de su clave preexistente `//`.
- `git diff --check` limpio.
- Sin despliegue ni cambios a partidas existentes.

Siguiente trabajo propuesto: resultados de descubrimiento redactados por el motor
y visibles en la interfaz; después ajustar pruebas obligatorias y reloj, y repetir
esta auditoría con el modelo de producción.
