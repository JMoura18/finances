#!/usr/bin/env bash
# Boot the backend and frontend in the background. Runs every time the
# codespace starts. Logs land in /tmp/cofre/*.log.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
mkdir -p /tmp/cofre

# Backend on :8000
(
  cd "$REPO_ROOT/backend"
  pkill -f 'uvicorn app.main:app' 2>/dev/null || true
  DATABASE_URL='sqlite+aiosqlite:///./cofre_dev.db' \
  ENVIRONMENT=dev \
  CORS_ORIGINS='["*"]' \
  nohup python3 -m uvicorn app.main:app \
    --host 0.0.0.0 --port 8000 \
    > /tmp/cofre/backend.log 2>&1 &
)

# Frontend on :5173
(
  cd "$REPO_ROOT/frontend"
  pkill -f 'vite' 2>/dev/null || true
  nohup npm run dev -- --host 0.0.0.0 --port 5173 \
    > /tmp/cofre/frontend.log 2>&1 &
)

echo "→ servers starting; tail logs with: tail -f /tmp/cofre/*.log"
