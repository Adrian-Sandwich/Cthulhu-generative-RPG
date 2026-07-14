#!/bin/bash
# THE LIGHTHOUSE — launcher (double-click me)
# Starts the web game on http://127.0.0.1:5001 and opens the browser.

cd "$(dirname "$0")" || exit 1

PORT="${PORT:-5001}"
URL="http://127.0.0.1:${PORT}"

echo "═══════════════════════════════════════════"
echo "  THE LIGHTHOUSE — Call of Cthulhu"
echo "═══════════════════════════════════════════"

# 1. Ollama must be running (the AI Dungeon Master)
if ! curl -s -o /dev/null --max-time 2 http://localhost:11434/api/tags; then
    echo "⚠️  Ollama no responde en :11434."
    echo "    Arráncalo primero (app de Ollama o 'ollama serve') y vuelve a intentar."
    read -r -p "Presiona ENTER para salir..."
    exit 1
fi
echo "✓ Ollama listo"

# 2. Free the port if a previous instance is still holding it
lsof -ti tcp:"${PORT}" 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

# 3. Launch the game server
echo "✓ Lanzando el juego en ${URL}"
FLASK_DEBUG=0 PORT="${PORT}" LOG_LEVEL=WARNING python3 app.py &
SERVER_PID=$!

# 4. Wait until it answers, then open the browser
for _ in $(seq 1 20); do
    if curl -s -o /dev/null --max-time 1 "${URL}/api/health"; then
        break
    fi
    sleep 0.5
done
open "${URL}"

echo ""
echo "  Juego corriendo. Cierra esta ventana (o Ctrl+C) para apagar el servidor."
echo ""

# Keep the window attached to the server; Ctrl+C / closing kills it
trap 'kill ${SERVER_PID} 2>/dev/null' EXIT
wait ${SERVER_PID}
