#!/usr/bin/env bash
# One-time install. Runs after the codespace is created.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "→ installing backend deps"
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet \
  fastapi 'uvicorn[standard]' 'sqlalchemy[asyncio]' aiosqlite \
  pydantic 'pydantic-settings' python-multipart httpx numpy

echo "→ installing frontend deps"
cd frontend
npm install --silent

echo "→ setup complete"
