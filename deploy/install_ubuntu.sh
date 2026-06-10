#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$APP_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[1/5] Checking Python"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "Python not found: $PYTHON_BIN" >&2
  exit 1
}

echo "[2/5] Creating virtualenv in $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "[3/5] Installing dependencies"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "[4/5] Preparing runtime folders"
mkdir -p "$APP_DIR/data" "$APP_DIR/generated_images"

echo "[5/5] Preparing .env"
if [[ ! -f "$APP_DIR/.env" ]]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo ".env created from .env.example. Fill in your keys before starting."
else
  echo ".env already present, left unchanged."
fi

echo "Install complete."
echo "Next: edit $APP_DIR/.env and run deploy/start_ubuntu.sh"
