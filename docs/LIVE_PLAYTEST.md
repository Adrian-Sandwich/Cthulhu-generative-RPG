# Prueba de rutas con el modelo real

`tools/playtest_live.py` recorre escape, transformación y destrucción usando los
handlers HTTP de Flask y el proveedor LLM configurado. Usa dados reales, sin
inyectar objetos, objetivos, ubicación ni resultados de tiradas. La estrategia
conoce el mapa: es una auditoría guiada, no una prueba ciega de descubrimiento.
No cubre el navegador, SSE ni la carga de producción.

El recorrido actualizado abre cada partida con una acción libre enviada al
modelo real. Después usa investigaciones explícitas del motor para las pistas
críticas, movimientos y decisiones finales. Por ello, terminar una ruta demuestra
su accesibilidad mecánica; no valida toda la prosa posible del narrador.

Ejemplo en PowerShell, con un modelo previamente instalado en Ollama:

```powershell
$env:LLM_MODEL = 'qwen2.5:3b'
.\.venv\Scripts\python.exe tools/playtest_live.py --output .runtime/live-route-audit
```

La carpeta de salida debe ser nueva. El script usa almacenamiento JSON aislado,
desactiva PostgreSQL y los subsistemas opcionales para esa ejecución y registra
peticiones, respuestas, duración, fallbacks y estado final en `transcript.json`.
No guarda claves del proveedor ni cookies en el informe. El modelo configurado
puede generar costes si se usa una API remota.

Cada objetivo admite tres intentos por defecto (`--attempts`). Una respuesta de
emergencia, error HTTP, combate que interrumpe el recorrido o falta de progreso
deja la ruta marcada como bloqueada. Un bloqueo por dados no demuestra que la
ruta sea imposible; no se repiten partidas hasta fabricar un resultado favorable.
El registro se actualiza después de cada petición para conservar evidencia si
se interrumpe la ejecución.

`--pace` separa las peticiones (3,2 segundos por defecto) para respetar el límite
de 20 acciones/tiradas por minuto. La auditoría posterior al ajuste de balance usa
`--attempts 8`; conserva los fallos reales, no modifica dados ni desactiva límites.

Para comprobar la interfaz en Chromium: instalar `playwright`, ejecutar
`python -m playwright install chromium` y `python tools/browser_smoke.py`. Esta
prueba usa un dado fijado únicamente para verificar la presentación de una pista;
no reemplaza la auditoría de rutas con dados reales. Guarda capturas de escritorio
y móvil, verifica SSE, inventario sin coste y recarga con dado pendiente.

Revisar el texto junto con ubicación, inventario y objetivos: que la API devuelva
200 no demuestra que la narración sea coherente ni que explique lo descubierto.
