# Deploying The Lighthouse (PaaS + hosted LLM)

Target: **Fly.io** (Docker + a persistent volume for saves) with the DM driven
by a hosted **OpenAI-compatible API** (Groq by default). No Ollama, no GPU.

## Why this shape
- `app.py` runs under **gunicorn** (gthread). JSON storage requires **1 worker**;
  PostgreSQL supports multiple workers and servers with shared coordination.
  gthread gives concurrency and supports the SSE streaming endpoint.
- The container filesystem is ephemeral. All persistence (saves, feedback,
  playtests, session key) is written under **`DATA_DIR`** → mount a volume there.
- Heavy/optional deps (chromadb, mem0ai, neo4j, torch) are **not** installed;
  every subsystem that uses them degrades gracefully.

## Environment / secrets
| Var | Value | Notes |
|-----|-------|-------|
| `LLM_PROVIDER` | `openai` | switches the client off Ollama |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | any OpenAI-compatible host |
| `LLM_MODEL` | `openai/gpt-oss-120b` | pick a Groq model |
| `LLM_API_KEY` | *(secret)* | Groq API key |
| `SECRET_KEY` | *(secret)* | `openssl rand -hex 32`; **must be stable** or sessions/resume break |
| `DATA_DIR` | `/data` | volume mount point |
| `MODERATION` | `local` | `local` / `off` / `api` — content moderation gate |
| `MODERATION_EXTRA` | *(optional)* | comma-separated extra terms for the local blocklist |
| `MODERATION_URL` | *(optional)* | override `/moderations` endpoint when `MODERATION=api` |
| `MODERATION_MODEL` | `omni-moderation-latest` | moderation model when `MODERATION=api` |
| `HOST`/`PORT` | `0.0.0.0`/`8080` | set in Dockerfile/fly.toml |

## Fly.io steps
```bash
fly launch --no-deploy               # creates app, keep the Dockerfile
fly volume create data --size 1      # 1 GB persistent disk → /data
fly secrets set SECRET_KEY=$(openssl rand -hex 32) LLM_API_KEY=<your-groq-key>
# edit app name / region in fly.toml if needed
fly deploy
fly open
```

## Railway / Render
Both read the `Dockerfile` (or the `Procfile`) directly. Set the same env vars
in the dashboard and attach a persistent volume mounted at `/data`.

## Local dev is unchanged
No env set → defaults to Ollama at `localhost:11434`, `DATA_DIR=.` (files in the
repo). `python app.py` or `./launch.command` as before.

## Before going public (see docs/ABUSE_POLICY.md)
- Per-IP rate limiting: **already on** (`RATE_LIMITS` in `web/context.py`).
- Content moderation on player input + LLM output: **already on** by default
  (`MODERATION=local` in `core/moderation.py`). For stronger coverage set
  `MODERATION=api` and provide an OpenAI-compatible `/moderations` endpoint.
- Run the automated regressions and review deployment-specific settings before release.

## Migrating existing playtest data
Copy `saves/`, `feedback/`, `playtests/` into the mounted volume (`/data`) to
carry over local playtest history:
```bash
fly ssh console -C "mkdir -p /data"
# then use `fly sftp shell` / `fly ssh sftp put` to upload the folders
```

## Proxy trust and rate limits

By default rate limits use the socket peer address and ignore forwarded IP
headers. Behind a reverse proxy, set `TRUSTED_PROXIES` to its actual source
addresses/CIDRs (comma-separated). Only trusted peers may supply
`X-Forwarded-For`; the application walks the chain from right to left and
stops at the first untrusted address. `CF-Connecting-IP` is ignored.
The proxy must append the observed client address or overwrite the header.
Do not trust arbitrary public/private networks. Without this configuration,
players behind a proxy share its rate-limit budget. Verify the peer address
in your deployment before setting it; there is no implicit platform trust.

## Interrupted turns

The browser saves `{action, action_id, game_id}` in per-tab `sessionStorage`
before sending a turn. On a broken stream or page reload, it queries
`GET /api/game/actions/<action_id>?game_id=<game_id>` until it obtains the
recorded result. If the server never received the action, the browser retries
the identical command. A duplicate ID returns the original result; reusing it
with different text or a different game is rejected with 409.

Receipts progress through `pending`, `running`, `completed` or `failed` and
live in the autosave's `app_state.actions`. The completed result and all turn
mechanics commit in one atomic file replacement. A restart encountering a
pending/running receipt marks it failed and restores the pre-turn checkpoint;
it does not automatically rerun the LLM. Storage failure cannot return success.
Receipts remain for the lifetime of the game and are cleared on start/reset.

An accepted streaming turn completes and saves even if the browser disconnects.
The session remains locked until its model call and consequences finish; other
mutations for that session wait. Status queries read the autosave without
waiting on generation. Disconnecting stops chunk delivery, not the model call.

API clients supplying an `action_id` must also send the `game_id` returned by
start/load/state. Legacy clients without an ID still work, but each request is
a new action and cannot safely retry an ambiguous response. IDs are 8–128 ASCII
letters, digits, underscores or hyphens. Cookies scope receipts to one player.

JSON storage remains a **one-process** design with a mounted data directory.
PostgreSQL adds shared persistence and locking, as described below. Neither
backend provides durable LLM jobs or token-by-token stream replay.
Roll/flee/start/reset are serialized but not covered by action idempotency.
Long games grow the receipt log. Browser recovery requires session storage.

## PostgreSQL and multiple servers

Set `CTHULHU_DATABASE_URL` to a PostgreSQL connection string and provide the
**same `SECRET_KEY` on every instance**. For existing players, use the original
signing key from your secret manager or the old `.flask_secret` file; changing
it invalidates their cookies. Never commit either secret.

Initialize the schema explicitly using the deployment environment:

```bash
python tools/migrate_postgres.py init
python tools/migrate_postgres.py import-json --data-dir /data
```

The second command is a dry run. Before the final import, stop the old
file-backed writers, back up `/data`, then run:

```bash
python tools/migrate_postgres.py import-json --data-dir /data --apply
```

The importer preserves source JSONs, skips identical existing rows and refuses
to overwrite conflicting rows. Resolve reported invalid/conflicting files
before switching traffic. Importing a receipt left `running` by a stopped
server is safe: the next owner marks it interrupted instead of rerunning it.
Historical feedback/playtest files are not imported by this command.

With PostgreSQL enabled, set `WEB_CONCURRENCY=2` (adjust after load testing) in
the Docker deployment, or launch gunicorn with the desired worker count.
Several instances may share the database; no sticky sessions are required.
There is **no automatic JSON fallback** if PostgreSQL is unavailable.

Each session operation acquires a session-level PostgreSQL advisory lock and
reloads the current snapshot. The lock connection is kept through generation,
but is in autocommit mode: no transaction remains open during the LLM call.
Every mutation writes through that same connection. If it is lost, the old
worker cannot reconnect and overwrite the next owner's state. PostgreSQL
releases the lock when the connection ends. Status reads use an independent
connection and can observe a running checkpoint immediately.

Use a **direct database connection or session-mode pooler**, never a
transaction-mode pooler. Budget at least one database connection per active
session operation plus capacity for status/admin requests. Statements have a
15-second timeout (including waiting for a busy lock); callers retry using
the same action ID. A lost commit acknowledgment is recovered from the stored
receipt rather than treated as permission to execute again.

Snapshots, action receipts, rate-limit budgets and new feedback are shared.
Admin save/feedback statistics read PostgreSQL. `active_sessions` and LLM health
counters remain local to the responding process. Generated images and optional
playtest export files remain under `DATA_DIR`: keep images disabled or provide
shared asset storage when using multiple hosts. `LLM_MAX_PARALLEL` now limits
in-flight calls per endpoint and process (defaults: Ollama 2, hosted provider 32).
`LLM_QUEUE_TIMEOUT` bounds admission wait (default 2 seconds, 0 rejects immediately).
Saturation uses the existing narrative/tool fallback without sending an API call.
Limits are per process; size all workers against the provider's global budget.

Short PostgreSQL operations reuse at most `PG_POOL_SIZE` connections per worker
(default 4; 0 disables reuse), with `PG_POOL_TIMEOUT` seconds of acquisition wait
(default 2) and at most 64 waiting callers. Exhaustion returns storage-unavailable
behavior, without JSON fallback. Session advisory locks still use dedicated
connections that close on scope exit: add those to the database connection budget.
Pools open lazily on first use in each worker and close at process exit. Do not
perform database requests in a pre-fork parent; an inherited opened pool is rejected.
Application owners creating many app instances in one process should call
`app.extensions['cthulhu'].store.close()` when disposing of each instance.

Pool lifecycle and connection checks follow the
[Psycopg pooling documentation](https://www.psycopg.org/psycopg3/docs/advanced/pool.html).

Keep the original JSON backup for rollback before cutover. After PostgreSQL
accepts new turns it is authoritative; switching back to the old JSON files
would lose that progress. Back up PostgreSQL with your normal database backup
policy. The runtime database role needs schema usage and DML permissions;
schema initialization should run under a migration role with DDL permissions.

The implementation follows PostgreSQL's [session advisory lock semantics](https://www.postgresql.org/docs/17/explicit-locking.html#ADVISORY-LOCKS)
and Psycopg's [autocommit behavior](https://www.psycopg.org/psycopg3/docs/basic/transactions.html#autocommit-transactions).

## Pruebas de capacidad

`REQUEST_TIMING=1` habilita registros JSON por petición hasta el cierre del stream,
con tiempos de conexión/bloqueo PostgreSQL y del modelo. Consultar
[observabilidad](OBSERVABILITY.md) para interpretar tiempos anidados y medir staging.

Antes de aumentar los procesos del despliegue, ejecutar el procedimiento de
[pruebas de carga](LOAD_TESTING.md). Incluye PostgreSQL real, alternancia entre
servidores, comprobaciones de repetición de comandos y un perfil separado para
verificar los límites de peticiones. El modelo se simula por defecto.

## Candidato de septiembre de 2026

Ver [evidencia y pendientes de salida](reports/release-readiness-20260925/README.md).
Los nuevos campos de pistas y recompensas viven en el documento de guardado;
no requieren una nueva tabla SQL. El importador se probó con una partida real de
la API, conservando cookie, inventario, pistas y recibos. Eso no sustituye una
copia de seguridad del volumen o base de datos de producción.

Antes del despliegue autorizado: autenticar Fly.io, inspeccionar el estado y
backend reales, respaldar sus datos y conservar la imagen anterior. Mantener un
worker si el backend sigue siendo JSON. No cambiar a PostgreSQL implícitamente:
la migración requiere detener los escritores y completar el procedimiento anterior.
Validar las rutas con las credenciales del modelo de producción antes de publicar.
Después, comprobar salud, reanudación de una partida y una acción real. Si se
revierte la imagen, conservar el almacén actual; no reemplazarlo con un respaldo
antiguo sobre partidas que ya hayan avanzado.
