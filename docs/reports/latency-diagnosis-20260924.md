# Diagnóstico instrumentado — 24 de septiembre de 2026

Se ejecutaron 448 turnos en 112 partidas, alternando entre dos procesos Waitress
de 16 hilos y PostgreSQL real. Los 448 recibos quedaron completados; no hubo
errores HTTP/SSE ni discrepancias de repetición, recibos o contador de turnos.
Los 448 streams tienen registro de servidor correlacionado con el cliente.
El modelo se simuló con 0.5 segundos por generación, sin llamadas facturables.

| Jugadores | Cierre cliente p95 (s) | WSGI p95 (s) | Conexiones PG p95 (s) | Bloqueo de partida PG p95 (s) | LLM acumulado p95 (s) | Fuera de WSGI p95 (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 1.4345 | 1.4299 | 0.3484 | 0.0009 | 1.0256 | 0.0255 |
| 32 | 1.8614 | 1.8585 | 0.6696 | 0.0011 | 1.1021 | 0.0454 |
| 64 | 2.7101 | 1.6769 | 0.5702 | 0.0013 | 1.1301 | 1.4738 |

Cada columna es un percentil independiente. No sumarlas. `Fuera de WSGI` se
calcula primero por petición correlacionada y después se obtiene el percentil;
incluye cola del servidor, red y trabajo del cliente. Las lecturas y escrituras
PG tuvieron p95 inferiores a 14 ms por petición en todos los niveles.

La adquisición del bloqueo de partida no domina esta carga de sesiones distintas.
La apertura repetida de conexiones sí tiene un coste relevante. A 64 clientes
crece mucho la demora fuera de WSGI; es consistente con esperar por los 32 hilos
disponibles, pero esta métrica no aísla la cola del servidor del resto del trayecto.
El tiempo LLM puede incluir varias generaciones por turno.

Los resultados varían entre ráfagas: esta pasada logró 21.23 turnos/s a 64 clientes,
frente a 14.92 en la pasada anterior sin instrumentación. No hubo una optimización
de capacidad en este cambio y no se atribuye esa diferencia a la instrumentación.
Hacen falta repeticiones y carga sostenida para estimar capacidad.

## Decisión siguiente

1. Evaluar un pool acotado para conexiones de operaciones cortas, midiendo su
   espera. Conservar la propiedad de la conexión que mantiene el advisory lock;
   reutilizarla sin liberar correctamente el bloqueo rompería la coordinación.
2. Implementar admisión al proveedor con espera acotada: `LLM_MAX_PARALLEL` se lee
   actualmente pero no se aplica. Multiplicar procesos no impone una cuota global.
3. Repetir en staging con Gunicorn, proveedor real y métricas del proxy antes de
   decidir el número de procesos. La CLI de Fly fue bloqueada por Windows Application
   Control incluso fuera del sandbox; no se consultó el estado remoto ni se desplegó.

La suite completa pasó con 214 pruebas tras instrumentar aplicación, PostgreSQL y
LLM. Tras añadir la correlación por ID, las 10 pruebas de medición e instrumentación
pasaron. Pyright reportó cero errores y las dos advertencias preexistentes de
`entity_graph.py`.

[Resultados y recursos](load-instrumented-20260924/report.md) ·
[Datos agregados y muestras del cliente](load-instrumented-20260924/results.json) ·
[Guía operativa](../OBSERVABILITY.md)
