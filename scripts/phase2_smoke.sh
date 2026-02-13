#!/usr/bin/env sh
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
LOG_FILE="/tmp/phase2_uvicorn.log"

if [ -z "${VIRTUAL_ENV:-}" ]; then
  echo "Virtualenv is not active. Please activate your venv and rerun."
  exit 1
fi

if lsof -iTCP:8001 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8001 is already in use. Please stop the process and retry."
  exit 1
fi

cd "$BACKEND_DIR"
uvicorn app.main:app --host 127.0.0.1 --port 8001 >"$LOG_FILE" 2>&1 &
UVICORN_PID=$!

cleanup() {
  kill -TERM "$UVICORN_PID" >/dev/null 2>&1 || true
  wait "$UVICORN_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ready=false
for _ in $(seq 1 30); do
  if curl --max-time 2 -s http://127.0.0.1:8001/health >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 0.2
done

if [ "$ready" != "true" ]; then
  echo "Server not ready on /health after waiting."
  if [ -f "$LOG_FILE" ]; then
    cat "$LOG_FILE"
  fi
  exit 1
fi

health_resp="$(curl --max-time 2 -s http://127.0.0.1:8001/health)"
if ! printf '%s' "$health_resp" | python -m json.tool >/dev/null 2>&1; then
  echo "Invalid JSON from /health"
  [ -f "$LOG_FILE" ] && cat "$LOG_FILE"
  exit 1
fi
health_pretty="$(printf '%s' "$health_resp" | python -m json.tool)"
expected_health="$(printf '%s' '{"status":"ok"}' | python -m json.tool)"
if [ "$health_pretty" != "$expected_health" ]; then
  echo "Unexpected /health response"
  [ -f "$LOG_FILE" ] && cat "$LOG_FILE"
  exit 1
fi

post_ok() {
  payload="$1"
  resp_file="$(mktemp /tmp/phase2_resp.XXXXXX)"
  status="$(curl -s -o "$resp_file" -w "%{http_code}" -H 'Content-Type: application/json' -d "$payload" http://127.0.0.1:8001/query)"
  if [ "$status" != "200" ]; then
    echo "Expected 200, got $status"
    [ -f "$LOG_FILE" ] && cat "$LOG_FILE"
    exit 1
  fi
  if ! python -m json.tool < "$resp_file" >/dev/null 2>&1; then
    echo "Invalid JSON response"
    [ -f "$LOG_FILE" ] && cat "$LOG_FILE"
    exit 1
  fi
}

post_ok '{"question":"عندي مشكلة في الفاتورة","category_hint":"billing","locale":"ar-SA","channel":"csr_ui"}'
post_ok '{"question":"التغطية ضعيفة في منطقتي","category_hint":"network","locale":"ar-SA","channel":"csr_ui"}'
post_ok '{"question":"asdf qwer zxcv","category_hint":"unknown","locale":"ar-SA","channel":"csr_ui"}'

status_empty="$(curl -s -o /tmp/phase2_empty.json -w "%{http_code}" -H 'Content-Type: application/json' -d '{"question":"","category_hint":"billing","locale":"ar-SA","channel":"csr_ui"}' http://127.0.0.1:8001/query)"
if [ "$status_empty" != "422" ]; then
  echo "Expected 422 for empty question, got $status_empty"
  [ -f "$LOG_FILE" ] && cat "$LOG_FILE"
  exit 1
fi

exit 0
