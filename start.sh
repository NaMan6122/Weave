#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT_DIR/apps/api"

echo "=== Weave - Starting all services ==="

# 1. Docker services (PostgreSQL + Redis)
echo "[1/4] Starting PostgreSQL and Redis..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d
echo "  Waiting for PostgreSQL to be ready..."
until docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T postgres pg_isready -U weave &>/dev/null; do
  sleep 1
done
echo "  PostgreSQL ready."

# 2. Python dependencies
echo "[2/4] Installing Python dependencies..."
cd "$API_DIR" && uv sync --quiet 2>/dev/null || uv sync
echo "  Dependencies installed."

# 3. Database migrations
echo "[3/4] Running database migrations..."
cd "$API_DIR" && uv run alembic upgrade head
echo "  Migrations complete."

# 4. Start API and Web
echo "[4/4] Starting API (FastAPI) and Web (Next.js)..."

# Kill processes on target ports (macOS syntax: need space before colon)
lsof -ti :8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti :3000 2>/dev/null | xargs kill -9 2>/dev/null || true

# Start API in background
cd "$API_DIR"
nohup uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/weave-api.log 2>&1 &
API_PID=$!
echo "  API starting (PID $API_PID)... http://localhost:8000"

# Start Web in background
cd "$ROOT_DIR"
nohup pnpm dev --filter=@weave/web > /tmp/weave-web.log 2>&1 &
WEB_PID=$!
echo "  Web starting (PID $WEB_PID)... http://localhost:3000"

# Wait for both to be ready (curl -f returns non-zero on HTTP errors)
echo "  Waiting for services to be ready..."
for i in $(seq 1 60); do
  api_ok=0; web_ok=0
  curl -sf -o /dev/null http://localhost:8000/docs 2>/dev/null && api_ok=1
  curl -sf -o /dev/null http://localhost:3000 2>/dev/null && web_ok=1
  [ "$api_ok" -eq 1 ] && [ "$web_ok" -eq 1 ] && break
  sleep 2
done

if curl -sf -o /dev/null http://localhost:8000/docs 2>/dev/null; then
  echo "  API:  http://localhost:8000"
else
  echo "  WARNING: API did not start (check /tmp/weave-api.log)"
fi

if curl -sf -o /dev/null http://localhost:3000 2>/dev/null; then
  echo "  Web:  http://localhost:3000"
else
  echo "  WARNING: Web did not start (check /tmp/weave-web.log)"
fi

echo ""
echo "=== Weave is running ==="
echo "  API:  http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "  Web:  http://localhost:3000"
echo ""
echo "Logs: tail -f /tmp/weave-api.log /tmp/weave-web.log"
echo "Stop: kill $API_PID $WEB_PID"
