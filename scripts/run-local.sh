#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/backend/.venv"

if [[ ! -x "$VENV/bin/uvicorn" ]]; then
  echo "Missing backend/.venv. Follow the setup steps in README.md first."
  exit 1
fi
if [[ ! -f "$ROOT/backend/.env" ]]; then
  echo "Missing backend/.env. Copy backend/.env.example and add your keys."
  exit 1
fi

"$VENV/bin/uvicorn" prism.main:app --app-dir "$ROOT/backend" --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT INT TERM

for _ in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null; then
    break
  fi
  sleep 0.25
done

cd "$ROOT"
npm run dev
