# Runbook

This runbook documents only commands and behavior currently defined in this repository.

## Prerequisites

- `python3` (CI pins Python `3.11` in `.github/workflows/lint_facts.yml`)
- `node` + `npm` (CI pins Node `20` in `.github/workflows/e2e_playwright.yml`)
- `make` (targets defined in `Makefile`)
- `curl` (used in `backend/README.md` verification commands)

`docker` and `docker compose` commands are documented in `backend/README.md` and are optional.

## Backend Setup and Run

From `backend/README.md`:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Also defined in `backend/README.md` quick verification:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

From `Makefile`:

```bash
make backend-run
```

## Frontend Setup and Run

Frontend scripts from `frontend/package.json`:

```bash
cd frontend
npm install
npm run dev
```

Single-command local dev from `Makefile` + `scripts/dev.sh`:

```bash
make dev
```

`scripts/dev.sh` starts:
- backend on `BACKEND_PORT` (default `8000`)
- frontend on `FRONTEND_PORT` (default `5173`)

## Test Commands Currently Defined

From `Makefile`:

```bash
make test
make backend-test
make phase2-smoke
make phase2-validate
make lint-facts
```

From `backend/README.md`:

```bash
cd backend
pytest -q tests/test_smoke.py
python3 -m compileall app
PYTHONPATH=. python3 scripts/smoke_quality.py
python3 ../scripts/lint_facts.py
```

From `frontend/package.json` and CI workflow:

```bash
cd frontend
npm run build
npm run validate
npm run test:e2e
npm run test:e2e:ui
npx playwright install --with-deps
```

Frontend unit test command is not currently defined in `frontend/package.json`.

## API Curl Examples

From `backend/README.md`:

Health:

```bash
curl -i http://127.0.0.1:8001/health
```

Metrics:

```bash
curl -s http://127.0.0.1:8001/metrics | python3 -m json.tool
```

Query:

```bash
curl -s http://127.0.0.1:8001/query -H 'Content-Type: application/json' -d '{"question":"كم سعر باقة 55 جيجا؟","locale":"ar-SA","channel":"csr_ui"}' | python3 -m json.tool
```

Raw query (no pipe):

```bash
curl -s http://127.0.0.1:8001/query -H 'Content-Type: application/json' -d '{"question":"كم سعر باقة 55 جيجا؟","locale":"ar-SA","channel":"csr_ui"}'
```

## Troubleshooting

### Address already in use

- Frontend E2E uses `127.0.0.1:5173` with `--strictPort` (`frontend/playwright.config.ts`).
- `make dev` uses defaults from `scripts/dev.sh`: backend `8000`, frontend `5173`.
- If these ports are busy, this repo does not define a process-kill command.
- You can run `make dev` with different ports because `scripts/dev.sh` reads env vars:

```bash
BACKEND_PORT=8001 FRONTEND_PORT=5174 make dev
```

### Rate limiting / 429 during manual testing

- Rate limiter is enabled by default (`backend/app/middleware/rate_limit.py`).
- Response shape includes `error_code` and `retry_after_seconds` with HTTP `429`.
- `/health` and `/metrics` are bypassed by limiter.
- For local/manual testing only, limiter bypass is defined via:

```bash
DISABLE_RATE_LIMIT=1 uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Playwright install/run issues

- Install browsers and system deps using the existing CI command:

```bash
cd frontend
npx playwright install --with-deps
```

- Run tests:

```bash
npm run test:e2e
```

- If dev server fails to bind to `5173`, update port usage when starting local dev (see Address section).

### Generated artifacts accidentally tracked in git

- CI guard already checks tracked artifacts in `.github/workflows/e2e_playwright.yml`.
- Local check command used by CI:

```bash
git ls-files | grep -En "frontend/playwright-report|frontend/test-results|__pycache__/|\.pyc$|\.pytest_cache/|^\.coverage(\.|$)"
```

- A repository-maintained cleanup script for untracking these files is not currently defined.
