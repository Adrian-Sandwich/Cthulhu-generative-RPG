# The Lighthouse — production image (PaaS: Fly.io / Railway / Render)
FROM python:3.11-slim

WORKDIR /app

# Install core deps only (optional subsystems degrade gracefully; not shipped).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistence: mount a volume here and set DATA_DIR=/data so saves, feedback,
# playtests and the session-signing key survive restarts.
ENV DATA_DIR=/data
RUN mkdir -p /data

ENV HOST=0.0.0.0 PORT=8080 FLASK_DEBUG=0
EXPOSE 8080

# Single worker: the session registry + per-session locks live in process
# memory (not shared across workers). gthread handles concurrency AND the SSE
# streaming responses; sync workers would buffer and break streaming.
CMD ["gunicorn", "--worker-class", "gthread", "--workers", "1", "--threads", "16", \
     "--timeout", "180", "--bind", "0.0.0.0:8080", "app:app"]
