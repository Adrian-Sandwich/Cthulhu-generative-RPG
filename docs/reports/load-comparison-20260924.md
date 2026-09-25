# Medición local de capacidad — 24 de septiembre de 2026

Dos servidores Waitress, 16 hilos por servidor, PostgreSQL local, Windows 11,
8 CPU lógicas y 15.73 GiB de RAM. Modelo simulado: 0.5 segundos por generación.
Cuatro turnos por jugador y partidas nuevas en cada nivel. Una generación no
equivale necesariamente a un turno: también hay introducciones y eventos.

## Cambio medido

El consumidor SSE esperaba hasta un segundo para comprobar que el trabajo había
terminado. Ahora el productor lo despierta al completar el resultado persistido.
El indicador de finalización sigue separado de la cola, y el hilo se espera antes
de liberar el bloqueo de partida, incluso si el consumidor se desconecta.

| Jugadores concurrentes | Cierre p95 antes (s) | Cierre p95 después (s) | Turnos/s antes | Turnos/s después |
|---:|---:|---:|---:|---:|
| 1 | 1.6600 | 1.0993 | 0.602 | 0.990 |
| 8 | 1.7074 | 1.1865 | 4.537 | 7.084 |
| 16 | 1.8782 | 1.3580 | 8.232 | 12.137 |
| 32 | 2.2601 | 1.8493 | 13.689 | 17.701 |
| 64 | 4.2158 | 3.5930 | 14.183 | 14.915 |

Cada pasada completó **484/484 turnos en 121 partidas**, sin errores HTTP/SSE
ni fallos en las verificaciones de repetición, recibos y contador de turnos.
Los 484 recibos terminaron en estado `completed`. El RSS máximo combinado de
servidores fue de 145.25 MiB antes y 145.04 MiB después.

A 32 jugadores, el p95 de cierre bajó aproximadamente 18% y el rendimiento subió
29%. A 64 jugadores el rendimiento deja de crecer y el p95 del primer texto sube
a 2.65 segundos: hay saturación en esta configuración. Los datos no aíslan cuánto
corresponde a hilos HTTP, conexiones PostgreSQL o competencia con el generador.
Son dos ráfagas comparables, no múltiples repeticiones con intervalos de confianza.

Fuentes: [línea base](load-baseline-20260924/report.md),
[comparación sin otras pruebas concurrentes](load-optimized-isolated-20260924/report.md).
La carpeta `load-optimized-20260924` corresponde a una pasada exploratoria que
coincidió parcialmente con pytest; queda excluida de esta comparación.

## Límites de peticiones

Con los límites normales y 8 clientes desde una sola IP, se admitieron 6 partidas
y se rechazaron 2 arranques con 429. De 20 acciones intentadas, 14 se completaron
y 6 recibieron 429. Las repeticiones de comprobación también consumen el presupuesto
de acciones. No hubo discrepancias de estado o duplicación observable.
Ver [resultado del perfil guardrails](load-guardrails-20260924/report.md).

## Modelo más lento

Con 3 segundos por generación y tres turnos por jugador:

| Jugadores | Turnos completados | Turnos/s | Primer texto p95 (s) | Cierre p95 (s) |
|---:|---:|---:|---:|---:|
| 8 | 24/24 | 1.503 | 0.9818 | 6.2453 |
| 32 | 96/96 | 5.300 | 1.5539 | 6.8163 |
| 64 | 192/192 | 5.277 | 7.1760 | 12.4381 |

Los 312 turnos terminaron sin errores ni discrepancias en las verificaciones.
De 32 a 64 jugadores, el rendimiento queda prácticamente igual y la latencia
crece: aumentar clientes no aumenta el trabajo completado por segundo.
Ver [resultado completo](load-slow-model-retry-20260924/report.md). Esta pasada
repite una ejecución interrumpida que no llegó a guardar un informe completo.

## Siguiente paso de escalamiento

Repetir en el entorno objetivo con Gunicorn y latencias representativas del proveedor.
Instrumentar tiempo en espera de un hilo HTTP, adquisición de conexión/bloqueo y
generación del modelo para atribuir la saturación antes de aumentar procesos o
introducir un pool. Después, fijar objetivos de latencia y error y realizar una
prueba sostenida con partidas largas. Esta medición no permite prometer una cifra
de usuarios de producción.

Comandos y alcance: [guía reproducible](../LOAD_TESTING.md).
