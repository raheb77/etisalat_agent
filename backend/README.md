# Backend (Phase 2)

## Scope
- Decision support only.
- Retrieval remains local/in-memory.
- Answer generation defaults to a local formatter and can be switched to Moonshot Kimi or Gemini via env.
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

Optional local env file:
- The backend automatically loads `backend/.env.local` at startup if it exists.
- Shell environment variables always override values from `backend/.env.local`.
- You do not need to run `source .env.local` before starting `uvicorn`.

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
- `backend/.env.local`
  - Optional repo-local file loaded automatically at startup.
  - Shell or system environment variables take precedence over file values.
- `DISABLE_LLM` (default: false)
  - Conceptual kill-switch for disabling the LLM adapter in later phases.
- `FACTS_DIR` (optional)
  - Override path to `knowledge/facts`.
- `LLM_PROVIDER` (default: `local`)
  - Supported values: `local`, `kimi`, `gemini`.
- `LLM_MODEL`
  - Optional override for the chat model name. Provider defaults are used when unset.
- `LLM_BASE_URL`
  - Optional override for the OpenAI-compatible API base URL. Provider defaults are used when unset.
- `KIMI_API_KEY`
  - Required when `LLM_PROVIDER=kimi`.
- `GEMINI_API_KEY`
  - Required when `LLM_PROVIDER=gemini`.
- `LLM_TIMEOUT_SECONDS` (default: `20`)
  - Request timeout for the answer-generation API call.

Example local setup for Kimi:
```bash
export LLM_PROVIDER=kimi
export LLM_MODEL=kimi-k2.5
export LLM_BASE_URL=https://api.moonshot.ai/v1
export KIMI_API_KEY=your_moonshot_api_key
```

Example local setup for Gemini:
```dotenv
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.1-flash-lite-preview
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_API_KEY=your_gemini_api_key
```

Equivalent shell setup for Gemini:
```bash
export LLM_PROVIDER=gemini
export LLM_MODEL=gemini-3.1-flash-lite-preview
export LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
export GEMINI_API_KEY=your_gemini_api_key
```

Run command after adding `backend/.env.local`:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Endpoints
- `GET /health`
- `POST /query`
