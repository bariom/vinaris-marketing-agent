#!/usr/bin/env bash
set -euo pipefail
umask 027

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$APP_DIR/.venv}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8123}"
WORKERS="${WORKERS:-2}"

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo ".env not found in $APP_DIR" >&2
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/gunicorn" ]]; then
  echo "gunicorn not found in $VENV_DIR. Run deploy/install_ubuntu.sh first." >&2
  exit 1
fi

cd "$APP_DIR"
chmod 600 "$APP_DIR/.env"
exec "$VENV_DIR/bin/gunicorn" \
  --bind "$HOST:$PORT" \
  --workers "$WORKERS" \
  --timeout 120 \
  "app.web:app"
