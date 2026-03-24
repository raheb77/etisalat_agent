# CSR Decision Support Agent

## What This Project Does

- Provides a FastAPI backend with `GET /health`, `POST /query`, and `GET /metrics`.
- Provides a React + Vite CSR UI that queries backend `/query` and renders answer details.
- Includes Playwright E2E tests with route interception and CI workflow execution.

## Quickstart

Run full stack with one command (defined in `Makefile` and `scripts/dev.sh`):

```bash
make dev
```

Manual backend setup/run (from `backend/README.md`):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Manual frontend setup/run (scripts in `frontend/package.json`):

```bash
cd frontend
npm install
npm run dev
```

## Tests

Repo-level and backend commands:

```bash
make test
make phase2-smoke
make phase2-validate
make lint-facts
```

```bash
cd backend
pytest -q tests/test_smoke.py
python3 -m compileall app
PYTHONPATH=. python3 scripts/smoke_quality.py
```

Frontend E2E:

```bash
cd frontend
npx playwright install --with-deps
npm run test:e2e
```

## Engineering Highlights

- In-memory telemetry and metrics endpoint (`/metrics`) with counters and latency statistics.
- Deterministic query decision path and safe fallback handling in backend routes.
- In-memory caching and rate limiting middleware in backend.
- CI workflows for facts linting and frontend Playwright E2E.
- Repository guard against committing generated artifacts in E2E workflow.
