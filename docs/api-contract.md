# CSR Query API Contract

## Endpoint
POST /query

## Request Example
```json
{
  "question": "string",
  "category_hint": "billing|network|...",
  "locale": "ar-SA",
  "channel": "csr_ui"
}
```

## Response Example
```json
{
  "answer": "string",
  "steps": ["string"],
  "citations": [
    {
      "source": "path",
      "chunk_id": "id",
      "score": 0.0
    }
  ],
  "confidence": 0.0,
  "category": "string",
  "risk_level": "low|medium|high",
  "handoff": true,
  "handoff_reason": "string",
  "handoff_payload": {
    "team": "string",
    "summary": "string",
    "evidence": ["string"]
  }
}
```

## Rules
- No PII in response.
- Citations must reference internal files only.
- No external URLs.

## Error Cases
- 401 Unauthorized
- 403 Forbidden
- 422 Validation Error
- 500 Internal Error
