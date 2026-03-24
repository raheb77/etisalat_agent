# 60-Second Demo Script

This demo flow is based on the current UI behavior and backend endpoints in this repository.

## Before You Start

1. Start the app stack:

```bash
make dev
```

2. Open the frontend URL printed by `scripts/dev.sh` (default: `http://localhost:5173`).
3. Keep a terminal open for backend requests and metrics checks.

## 60-Second Flow

1. Show the chat UI and send:
   - `كم سعر باقة 55 جيجا؟`
2. In the response area, show:
   - assistant TL;DR bubble
   - full response panel
   - confidence
   - category
   - citations list
3. Switch locale from `ar-SA` to `en-US` and show directionality change in the response panel (`dir`).
4. Send:
   - `عندي مشكلة`
   Show the clarification-style answer and no-citations state.
5. Optional: send repeated `/query` requests to demonstrate limiter behavior (HTTP `429` from backend middleware).

## Backend Proof Points to Show

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

What to point out:
- `/metrics` contains counters and latency stats.
- `/query` returns `answer`, `citations`, `confidence`, `category`, and `handoff`.

## Media Placeholders

- GIF placeholder: `docs/assets/ui.gif`
- PNG placeholder: `docs/assets/ui.png`
