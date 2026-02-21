# Backend (Phase 2)

## Scope
- Decision support only.
- No external retrieval or LLM calls yet.
- PII is masked before model handling and never logged raw.

## Production-Inspired Demo Notes
This backend includes production-inspired behaviors (telemetry, rate limiting, caching, fallback strategies) but remains a demo implementation with in-memory state.

## Local run
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Local Verification
```bash
cd backend
pytest -q tests/test_smoke.py
```

## Quick Verification
```bash
python3 -m compileall app
```

```bash
PYTHONPATH=. python3 scripts/smoke_quality.py
```

```bash
python3 ../scripts/lint_facts.py
```

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

```bash
curl -i http://127.0.0.1:8001/health
```

```bash
curl -s http://127.0.0.1:8001/query -H 'Content-Type: application/json' -d '{"question":"كم سعر باقة 55 جيجا؟","locale":"ar-SA","channel":"csr_ui"}' | python3 -m json.tool
```

```bash
curl -s http://127.0.0.1:8001/query -H 'Content-Type: application/json' -d '{"question":"كم سعر باقة 55 جيجا؟","locale":"ar-SA","channel":"csr_ui"}'
```

```bash
curl -s http://127.0.0.1:8001/metrics | python3 -m json.tool
```

Note: if you see zsh `unknown file attribute: ^`, retype the command manually (avoid pasting from PDF/web).

Expected outputs:
- `/health` returns `{"status":"ok"}`.
- `/metrics` returns JSON with `counters` and `latency_ms` stats.
- `/query` returns JSON with `answer`, `citations`, `confidence`, and `handoff`.

## Facts Frontmatter
Fact markdown files require YAML frontmatter (`---` ... `---`) with:
- `fact_id` (or `id`)
- `tags` (non-empty list)
- `source`
- `updated_at` (ISO date) or a `YYYYMMDD_` filename prefix

Optional fields:
- `title` (if omitted, the linter falls back to the `Statement:` line)
- `locale`

Run the linter locally:
```bash
python3 ../scripts/lint_facts.py
```

## Observability
- `GET /metrics` returns in-memory counters and latency stats for the last samples.
- Sample:
```bash
curl -s http://127.0.0.1:8001/metrics | python3 -m json.tool
```

## Debugging
- Add `X-Debug: 1` header to `/query` to include `debug.decision_path` in the response.
- Example:
```bash
curl -s http://127.0.0.1:8001/query -H 'X-Debug: 1' -H 'Content-Type: application/json' -d '{"question":"عندي مشكلة","locale":"ar-SA","channel":"csr_ui"}' | python3 -m json.tool
```

## Caching
- In-memory TTL cache (default 60s, max 256 items).
- Cached only when: handoff=false, did_fallback=false, is_oos=false, is_ambiguous=false, and category != fraud.

## Rate Limiting
- Simple in-memory sliding window: 30 requests per 60 seconds per (client_ip, channel).
- Cache hits (including negative cache) use a separate allowance to reduce burst 429s.
- `/health` and `/metrics` are not rate-limited.
- Quick test (run 35 times):
```bash
for i in {1..35}; do curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/health; done
```

## Cost Awareness
- Tokens are estimated by text length heuristic (no external tokenizer).
- Cost estimates are 0.0 by default.
- Configure via env:
  - `LLM_PRICE_PER_1K_IN`
  - `LLM_PRICE_PER_1K_OUT`

## Failure Strategy
- Deterministic fallback reason codes are used for retrieval/ranking/answer errors.
- Safe user-facing Arabic message is returned for failures.

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
