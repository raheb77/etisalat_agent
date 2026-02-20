from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_rate_limit_returns_retry_after(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("DISABLE_RATE_LIMIT", "0")
    payloads = [
        {"question": f"rate limit {i}", "locale": "ar-SA", "channel": "rate_limit"}
        for i in range(12)
    ]
    status_codes = []
    last_429 = None
    for payload in payloads:
        resp = client.post("/query", json=payload)
        status_codes.append(resp.status_code)
        if resp.status_code == 429:
            last_429 = resp
            break

    assert any(code == 429 for code in status_codes), "Expected a 429 response"
    assert last_429 is not None
    body = last_429.json()
    assert body.get("error_code") == "rate_limited"
    assert "retry_after_seconds" in body
    assert last_429.headers.get("Retry-After")
