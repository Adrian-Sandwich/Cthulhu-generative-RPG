# Deploying The Lighthouse (PaaS + hosted LLM)

Target: **Fly.io** (Docker + a persistent volume for saves) with the DM driven
by a hosted **OpenAI-compatible API** (Groq by default). No Ollama, no GPU.

## Why this shape
- `app.py` runs under **gunicorn** (gthread, **1 worker**). The per-session game
  registry and locks live in process memory, so it must stay single-process;
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
| `LLM_MODEL` | `llama-3.3-70b-versatile` | pick a Groq model |
| `LLM_API_KEY` | *(secret)* | Groq API key |
| `SECRET_KEY` | *(secret)* | `openssl rand -hex 32`; **must be stable** or sessions/resume break |
| `DATA_DIR` | `/data` | volume mount point |
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
- Per-IP rate limiting: **already on**.
- Content moderation on player input + LLM output: **not yet** — add before a
  truly open launch.
- The security review of the current branch found no exploitable issues.

## Migrating existing playtest data
Copy `saves/`, `feedback/`, `playtests/` into the mounted volume (`/data`) to
carry over local playtest history:
```bash
fly ssh console -C "mkdir -p /data"
# then use `fly sftp shell` / `fly ssh sftp put` to upload the folders
```
