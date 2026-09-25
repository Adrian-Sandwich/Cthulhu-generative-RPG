# Pistas, inventario y preparación de salida

**Desplegado y comprobado el 25 de septiembre de 2026** en
[lighthouse-cthulhu.fly.dev](https://lighthouse-cthulhu.fly.dev/).

## Implementado y verificado localmente

- Inventario y munición visibles en `[inventory & clues]`; consultas `inventory`
  e `inventario` sin gastar turno ni usar el modelo. Disponibles con dado pendiente.
- Diario de hallazgos confirmados y botones de acciones válidas en el lugar actual.
- Investigaciones esenciales explícitas con dificultad Normal. El motor redacta
  el hallazgo exitoso o el coste del fallo; el narrador no puede omitir esa pista.
- Reloj de 40 turnos para partidas nuevas; guardados existentes conservan el suyo.
- Recarga del navegador restaura partidas aunque no hubiera una acción en curso.
- Exclusión de secretos, temporales y partidas de auditoría del contexto Docker.

## Evidencia

La [transcripción](transcript.json) registra **76 peticiones y cero fallbacks**.
Modelo local real `qwen2.5:3b`, académico, dados reales, hasta ocho intentos por
objetivo y pausas de 3,2 segundos para respetar los límites. Una acción libre por
partida consulta al modelo; las investigaciones esenciales posteriores son del motor.

| Final | Resultado | Turno final |
|---|---|---|
| Escape | Completado | 4 |
| Transformación | Completado | 29 |
| Destrucción | Completado | 26 |

Los tres recorridos terminaron antes de la presión de tiempo. Esta muestra no
garantiza victorias ni mide el balance de todas las profesiones. Una ejecución
anterior sin pausas encontró HTTP 429; se corrigió el ritmo del ejecutor sin
relajar el límite del servidor.

**307 pruebas pasan**, con PostgreSQL real, migración y frontend. La nueva prueba
de migración importa un guardado generado por la API, vuelve a abrirlo en una
aplicación PostgreSQL con la misma cookie y comprueba inventario, hallazgos y
repetición exacta de un recibo. Se verifica importación en seco, aplicada e idempotente.

Chromium comprobó recogida por SSE, consulta en español sin coste, inventario con
dado pendiente, botones bloqueados durante la tirada, recarga de partida y pista,
y ancho móvil. Su dado se fija para esa comprobación visual, por separado de los
dados reales del recorrido. Capturas: [escritorio](inventory-desktop.png),
[móvil](inventory-mobile.png). No hubo errores JavaScript de página.

Pyright: cero errores; dos advertencias preexistentes en `entity_graph.py` y la
clave de configuración `//`. `git diff --check` limpio. La validación local usa
Python 3.14; CI y Docker siguen en 3.11 y no se ejecutaron remotamente en esta sesión.

## Validación remota y candidato de despliegue

Fly.io ya está autenticado. Se verificó una máquina (`897356b62d06e8`) con JSON
y 20 archivos de partidas en `/data/saves/generative`. Se conservaron sus huellas
SHA-256 localmente, sin publicar contenido de jugadores. El volumen
`vol_vxm0mz2m87dm29j4` tiene el respaldo previo al despliegue
`vs_77mlRKPZV40uevak0XMO4lm`, confirmado como `created`, con retención de cinco días.

La primera auditoría remota encontró **HTTP 401** con la clave anterior:
[evidencia histórica](groq-audit.json). El usuario renovó el secreto y se activó
en Fly.io sin mostrar ni copiar su valor. Después se repitió la auditoría en
`/tmp`, con Python 3.11.16 y las dependencias de producción, sin modificar las
partidas existentes.

La [auditoría con Groq y la clave renovada](groq-renewed-audit.json) completó los
tres finales: escape en turno 4, transformación en 36 y destrucción en 25.
**90 peticiones, cero fallbacks**, dados reales y modelo `openai/gpt-oss-120b`.
Las investigaciones esenciales usan texto del motor; las acciones libres y sus
consecuencias no esenciales sí consultan al modelo. No es una garantía semántica
para toda posible narración.

Se restauraron copias temporales de las **20 partidas de producción**, sin
errores y sin cambiar los originales: [compatibilidad](compatibility.json).

Imagen publicada:
`registry.fly.io/lighthouse-cthulhu:release-20260925-candidate` (52 MB), digest
`sha256:2f446803f8c554e39560658250fb4bf6924ccb3ce05a2332ee19c42cb10b417d`.
Se actualizó únicamente la máquina existente, sin crear réplicas, manteniendo
JSON y el volumen original. Se volvió a aplicar `fly.toml`, incluida la suspensión
automática habitual. Fly completó sus comprobaciones de despliegue y DNS.

Imagen anterior conservada como referencia para reversión:
`registry.fly.io/lighthouse-cthulhu:deployment-01M0XMBAZH6DA1DPENDQDN28N3`.
Una reversión de imagen debe preservar el volumen actual; no restaurar un respaldo
antiguo encima de partidas que hayan avanzado después del despliegue.

## Comprobaciones posteriores a la publicación

La [prueba sobre la web pública](production-smoke.json) verificó salud, reloj de
40 turnos, recogida única, repetición exacta del recibo, inventario sin coste,
rechazo HTTP 422 de etiquetas falsas, respuesta real de Groq y recuperación de
inventario/turno/tirada. Chromium abrió la sesión recuperada y comprobó el panel
en escritorio y móvil, sin errores JavaScript. Capturas de producción:
[escritorio](production-desktop.png), [móvil](production-mobile.png).

La partida creada exclusivamente para la verificación se eliminó mediante su
propia sesión. Las **20 partidas anteriores permanecen idénticas**, comparadas
por SHA-256 antes y después: [integridad](save-integrity.json). El contador de
respuestas de emergencia siguió en cero. No se migró a PostgreSQL ni se cambió
la clave de firma de las sesiones.
