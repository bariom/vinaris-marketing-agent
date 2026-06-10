#!/usr/bin/env bash
set -euo pipefail
umask 027

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$APP_DIR/.venv}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-}"

cd "$APP_DIR"

echo "[1/4] Fetching latest code"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "[2/4] Updating Python dependencies"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "[3/4] Ensuring runtime folders"
mkdir -p "$APP_DIR/data" "$APP_DIR/generated_images" "$APP_DIR/exports"
if [[ -f "$APP_DIR/.env" ]]; then
  chmod 600 "$APP_DIR/.env"
fi
chmod 700 "$APP_DIR/data" "$APP_DIR/generated_images" "$APP_DIR/exports"

echo "[4/4] Restarting service if configured"
if [[ -n "$SERVICE_NAME" ]]; then
  sudo systemctl restart "$SERVICE_NAME"
  sudo systemctl status "$SERVICE_NAME" --no-pager
else
  echo "SERVICE_NAME not set, skipping restart."
fi

echo "Update complete."
