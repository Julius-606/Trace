#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEBATEHUB_DIR="${APP_DIR}/DebateHub"
DEBATEHUB_PID=""

cd "${APP_DIR}"

cleanup() {
  if [[ -n "${DEBATEHUB_PID}" ]]; then
    kill "${DEBATEHUB_PID}" 2>/dev/null || true
    wait "${DEBATEHUB_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ -f "${DEBATEHUB_DIR}/server.js" ]]; then
  (
    cd "${DEBATEHUB_DIR}"
    PORT=3000 DEBATEHUB_PORT=3000 node server.js
  ) &
  DEBATEHUB_PID=$!
fi

if [[ -x "${APP_DIR}/../.venv/bin/uvicorn" ]]; then
  UVICORN_BIN="${APP_DIR}/../.venv/bin/uvicorn"
else
  UVICORN_BIN="uvicorn"
fi

exec "${UVICORN_BIN}" app.main:app --host 0.0.0.0 --port "${PORT:-7860}"
