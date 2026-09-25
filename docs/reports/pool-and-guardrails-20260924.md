# Pool, admisión y guardrails — 24 de septiembre de 2026

Se añadió un pool acotado para operaciones cortas de PostgreSQL. Las conexiones
que sostienen advisory locks siguen siendo dedicadas y se cierran al liberar la
partida. El límite de concurrencia por endpoint del modelo ahora se aplica con
espera acotada y liberación del permiso en `finally`, incluso al cancelar.

## Comparación local

Dos procesos, 16 hilos por proceso, 32 y 64 jugadores, cuatro turnos por jugador.
Modelo simulado de 0.5 segundos por generación. Ambas pasadas tienen los mismos
guardrails y retienen la narración completa hasta validarla; la única opción
distinta es `--pg-pool-size 0` frente a `--pg-pool-size 4`.

| Jugadores | Cierre p95 sin pool (s) | Con pool (s) | Turnos/s sin pool | Con pool |
|---:|---:|---:|---:|---:|
| 32 | 1.6509 | 1.6237 | 19.696 | 22.090 |
| 64 | 2.8911 | 2.5154 | 21.474 | 23.385 |

Cada pasada completó **384/384 turnos**, sin errores ni discrepancias de estado.
A 64 jugadores el p95 de cierre bajó aproximadamente 13% y el rendimiento subió
9%. El p95 de la verificación del presupuesto de peticiones bajó de 343 a 46 ms;
la adquisición de conexión del pool tuvo p95 de 28 ms. La apertura de la conexión
dedicada al bloqueo de partida sigue teniendo coste (p95 de 389 ms).

Es una comparación corta, no una estimación de capacidad garantizada ni de
significancia estadística. El simulador sustituye `LLMClient.chat`: las garantías
de admisión LLM se prueban separadamente, sin llamadas a un proveedor real.
No se ha desplegado ni ejecutado carga remota.

## Validación de comportamiento

La suite completa pasó con **251 pruebas**. Incluye reutilización real de una
conexión PostgreSQL, agotamiento acotado del pool, recuperación de una conexión
terminada y separación respecto a conexiones con locks. Tras serializar también
la inicialización del selector LLM, pasaron sus cinco pruebas de admisión y cancelación.
Pyright terminó con cero errores y dos advertencias preexistentes.

Los guardrails bloquean patrones conocidos de instrucciones y dados falsificados;
comprueban narración antes de SSE, acotan cálculos de dados, agregan los topes de
daño por turno y verifican la ubicación de objetos. La prueba de narración maliciosa
confirma que no aparece en SSE y que el estado se restaura. Los escenarios de
recogida legítima se actualizaron para situar al jugador en la habitación del objeto.

La validación completa añade espera antes del primer texto. No se presenta como
un filtro semántico infalible: ver [límites y casos pendientes](../DM_GUARDRAILS.md).

[Pasada sin pool](load-pool-off-20260924/report.md) ·
[Pasada con pool](load-pool-on-20260924/report.md) ·
[Configuración operativa](../DEPLOY.md)
