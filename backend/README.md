# Backend (Phase 2)

## Scope
- Decision support only.
- No external retrieval or LLM calls yet.
- PII is masked before model handling and never logged raw.

## Local run
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Phase 2 smoke validation
Run from repo root:
```bash
./scripts/phase2_smoke.sh
```

## Docker run
```bash
docker build -t csr-backend ./backend
docker run -p 8000:8000 csr-backend
```

## Docker Compose
```bash
docker compose up --build
```

## Environment variables
- `DISABLE_LLM` (default: false)
  - Conceptual kill-switch for disabling the LLM adapter in later phases.
- `FACTS_DIR` (optional)
  - Override path to `knowledge/facts`.

## Endpoints
- `GET /health`
- `POST /query`
