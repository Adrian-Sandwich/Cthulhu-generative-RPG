# Pruebas de carga reproducibles

Para atribuir latencia a conexión, bloqueo y modelo, añadir `--request-timing`.
Ver [instrumentación y alcance de las métricas](OBSERVABILITY.md).

El generador levanta dos procesos HTTP locales con Waitress y usa PostgreSQL real.
Cada jugador alterna entre servidores; comprueba el recibo persistido, la repetición
del primer comando y el contador final de turnos. No requiere una partida existente.

## Ejecución

Instalar `requirements-dev.txt`. Preparar una base PostgreSQL dedicada a pruebas;
el usuario necesita permiso para crear y eliminar esquemas. En PowerShell:

```powershell
$env:CTHULHU_TEST_DATABASE_URL = 'host=127.0.0.1 dbname=cthulhu_test user=postgres'
.\.venv\Scripts\python.exe tools/load_test.py --levels 1,8,16,32,64 --turns 4 --model-seconds 0.5 --output docs/reports/my-capacity-run
.\.venv\Scripts\python.exe tools/load_test.py --profile guardrails --levels 8 --turns 4 --model-seconds 0.5 --output docs/reports/my-guardrail-run
```

Usar un directorio de salida nuevo por ejecución y ejecutar las mediciones en serie,
sin otras pruebas o cargas concurrentes. En Linux, sustituir el ejecutable por
`.venv/bin/python`. Cada ejecución crea un esquema aleatorio `cthulhu_load_*` y lo
elimina al terminar, junto con sus procesos y datos temporales. Una terminación
forzada del generador puede impedir esa limpieza; los nombres de esquema no son
esquemas de producción. Nunca apuntar la variable a una base de producción.

Por defecto, las llamadas al modelo se simulan y no consumen API. El retraso indicado
es **por generación**, no por turno: introducciones y eventos pueden generar llamadas
adicionales. El grafo de entidades, imágenes y moderación remota están deshabilitados.
La simulación sustituye `LLMClient.chat`: no mide el transporte, reintentos ni
control de concurrencia interno del cliente del proveedor.
`--live-model` permite expresamente llamadas facturables al proveedor configurado;
no se ha utilizado para los resultados incluidos. Un final de partida puede acortar
la ejecución real: revisar siempre `requested_turns`, `attempted` y `completed`.

## Interpretación

- `capacity` amplía los límites de peticiones únicamente en la aplicación temporal.
  Cualquier rechazo HTTP o fallo de integridad produce una salida distinta de cero.
- `guardrails` conserva los límites habituales. Todos los clientes comparten la IP
  local; los rechazos 429 se registran y están permitidos en este perfil.
- Los clientes son de bucle cerrado, sin tiempo para pensar entre acciones. El
  arranque de partidas queda fuera del tiempo de cada etapa. Las verificaciones
  entre servidores sí forman parte del tiempo usado para calcular turnos/segundo.
- Se mide primer fragmento de narración y cierre completo del stream. Los percentiles
  sólo incluyen turnos exitosos; los errores aparecen por separado, incluidos errores
  SSE que llegan con HTTP 200 y respuestas sin evento terminal.
- La memoria es el máximo muestreado de RSS combinado de los procesos servidores;
  no incluye PostgreSQL ni el generador. El CPU también corresponde sólo a servidores.
- `results.json` conserva los resultados y configuración; `report.md` los resume.
  Las comprobaciones de repetición y contador detectan duplicación observable, pero
  esta carga no sustituye las pruebas de fallos y recuperación de PostgreSQL.

Waitress usa un número fijo de hilos por proceso ([documentación oficial](https://docs.pylonsproject.org/projects/waitress/en/latest/design.html)).
Con streams largos, esos hilos permanecen ocupados. Los resultados de esta máquina
Windows no establecen capacidad de producción en Gunicorn: son ráfagas cortas, con
cliente, aplicación y base de datos en el mismo equipo. Antes de dimensionar usuarios,
repetir en el despliegue objetivo con latencias y cuotas reales del proveedor, sesiones
largas, distribución de acciones y tiempo de lectura representativos.
