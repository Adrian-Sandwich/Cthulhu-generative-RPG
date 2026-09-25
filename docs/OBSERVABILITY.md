# Diagnóstico de latencia

Activar `REQUEST_TIMING=1` en el entorno antes de arrancar los servidores.
No requiere migración ni servicios adicionales. Por defecto está desactivado.
Se emite un registro JSON por petición a stderr, con `event=request_timing`,
PID, un identificador generado por el servidor, plantilla de ruta, estado HTTP,
duración WSGI y tiempos de las operaciones instrumentadas. El identificador
también se entrega como cabecera `X-Request-ID`.

Los registros no contienen acciones, narración, cookies, consultas, direcciones
del cliente, identificadores de partida, DSN ni claves del proveedor. Rutas
desconocidas se agrupan como `<unmatched>`; los parámetros de rutas conocidas
se conservan como plantillas, por ejemplo `<action_id>`.

## Qué mide cada campo

| Campo | Alcance |
|---|---|
| `seconds` | Desde entrada a WSGI hasta agotamiento, error o cierre de la respuesta; incluye la iteración SSE |
| `session.local_lock` | Adquisición del bloqueo local de la partida |
| `postgres.connect` | Apertura de conexiones PostgreSQL, incluidos intentos fallidos |
| `postgres.pool_wait` | Adquisición y comprobación de una conexión reutilizable para operaciones cortas |
| `postgres.session_lock` | Consulta de adquisición del advisory lock; incluye el viaje a la base de datos |
| `postgres.read` | Lectura y decodificación del snapshot |
| `postgres.write` | Serialización, escritura y confirmación de un snapshot |
| `postgres.rate_limit` | Verificación completa del presupuesto, incluida su conexión y transacción |
| `llm.endpoint_selection` | Selección y espera acotada de un permiso por endpoint y proceso |
| `llm.chat` / `llm.tools` | Llamada completa al cliente del modelo, incluidos reintentos y entrega de fragmentos |

Cada operación tiene `seconds` acumulados, `calls` y `errors` (excepciones que
salieron del tramo). Los tiempos anidados **se superponen**: no sumarlos para
obtener la duración total. Una respuesta de fallback del modelo no es una
excepción y no incrementa `errors`. La entrega de fragmentos puede esperar a un
consumidor lento, por lo que `llm.chat` no equivale a tiempo puro de inferencia.

`outcome=exhausted` indica que WSGI agotó el iterable; `closed`, que se cerró antes
(por ejemplo una desconexión); `exception`, una excepción que salió de WSGI.
No confundirlos con éxito del turno: SSE puede entregar un evento `error` bajo
HTTP 200. El generador de carga verifica por separado los eventos terminales.
El hilo que genera un turno hereda el contexto de medición y su cierre sigue
esperando a que termine el guardado. Fallos del destino de logs no rompen la partida.

## Reproducir el diagnóstico local

```powershell
$env:CTHULHU_TEST_DATABASE_URL = 'host=127.0.0.1 dbname=cthulhu_test user=postgres'
.\.venv\Scripts\python.exe tools/load_test.py --request-timing --levels 16,32,64 --turns 4 --model-seconds 0.5 --output docs/reports/my-instrumented-run
```

Se guardan `timings-0.jsonl`, `timings-1.jsonl`, `results.json` y `report.md`.
Los percentiles de operaciones se calculan sobre el tiempo acumulado por petición
de stream, tomando cero si la operación no ocurrió. Revisar `records` y
`paired_records` junto al número de turnos; una ejecución cortada puede dejar
registros incompletos. Los archivos contienen también arranques y verificaciones,
pero el resumen de tiempos del servidor filtra exclusivamente la ruta de stream.

En `results.json`, `outside_wsgi` resta la duración del servidor de la del cliente
**para la misma petición**, usando `X-Request-ID`. Incluye espera en el servidor
antes de WSGI, red y trabajo del cliente; no es una medida exclusiva de cola HTTP.
Pueden aparecer pequeños valores negativos por diferencias de límites de medición.
Los relojes no necesitan estar sincronizados: se restan duraciones, no timestamps.

## Medir en el despliegue objetivo

El harness actual crea servidores locales; no envía carga a una URL remota.
Para medir Gunicorn y un proveedor real, preparar un entorno de staging separado,
con base y claves de prueba, habilitar `REQUEST_TIMING=1`, y recoger los logs
de todos los procesos durante una carga autorizada. Correlacionar tiempos del
cliente mediante la cabecera. Registrar workers, hilos, límites del proxy,
latencias y cuotas del proveedor y duración de la prueba junto con los resultados.
La espera anterior a WSGI requiere correlación externa o instrumentación específica
del servidor; esta implementación no la presenta como una medición directa.

No se desplegaron estos cambios ni se ejecutó carga remota: la consulta de estado
con `flyctl` fue bloqueada por Windows Application Control, también fuera del sandbox.

El selector aplica `LLM_MAX_PARALLEL`, con espera acotada por `LLM_QUEUE_TIMEOUT`.
El límite por proceso no sustituye la cuota global del proveedor. El harness simulado
sustituye el transporte LLM; la admisión se comprueba separadamente en pruebas de
concurrencia, saturación y cancelación.

Desde la incorporación de guardrails, la narración del modelo se valida completa
antes de entregarla a SSE. El primer texto mide ahora narración validada; no es
tiempo al primer token del proveedor. Comparar rendimiento con y sin pool usando
esta misma política, mediante `--pg-pool-size 0` y `--pg-pool-size 4`.

Usar los registros para comparar conexión/bloqueo/modelo y decidir el siguiente
cambio. Una muestra corta con un modelo simulado no establece capacidad de producción.
