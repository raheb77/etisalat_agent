from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from typing import Callable, Dict, List, Optional, Tuple, Union

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _post_query(question: str) -> Tuple[Optional[Dict[str, object]], str]:
    payload = {
        "question": question,
        "locale": "ar-SA",
        "channel": "csr_ui",
    }
    response = client.post("/query", json=payload)
    raw_text = response.text
    try:
        body = response.json()
    except ValueError:
        return None, raw_text
    if response.status_code != 200:
        return None, raw_text
    return body, ""


def _get_metrics() -> Tuple[Optional[Dict[str, object]], str]:
    response = client.get("/metrics")
    raw_text = response.text
    try:
        body = response.json()
    except ValueError:
        return None, raw_text
    if response.status_code != 200:
        return None, raw_text
    return body, ""


def _sum_counters(metrics: Dict[str, object], prefix: str) -> int:
    counters = metrics.get("counters", {})
    if not isinstance(counters, dict):
        return 0
    total = 0
    for key, value in counters.items():
        if isinstance(key, str) and key.startswith(prefix) and isinstance(value, int):
            total += value
    return total


def _sum_latency_count(metrics: Dict[str, object], prefix: str) -> int:
    latency = metrics.get("latency_ms", {})
    if not isinstance(latency, dict):
        return 0
    total = 0
    for key, stats in latency.items():
        if not (isinstance(key, str) and key.startswith(prefix)):
            continue
        if isinstance(stats, dict):
            count = stats.get("count", 0)
            if isinstance(count, int):
                total += count
    return total


def _confidence_pct(body: Dict[str, object]) -> int:
    value = body.get("confidence", 0)
    if isinstance(value, (int, float)):
        if value <= 1:
            return int(round(value * 100))
        return int(round(value))
    return 0


def _contains(text: str, needle: str) -> bool:
    return needle in text


def _clarification_requested(text: str) -> bool:
    return any(phrase in text for phrase in ["غير واضح", "تفاصيل", "clarify", "details"])


def run_case(question: str, predicate: Callable[[Dict[str, object]], bool]) -> Dict[str, object]:
    try:
        body, error_text = _post_query(question)
    except Exception as exc:
        print(f"Request failed for '{question}': {exc}")
        return {
            "query": question,
            "confidence": 0,
            "handoff": False,
            "reason": "request_error",
            "citations_count": 0,
            "passed": False,
        }

    if body is None:
        print(f"Non-JSON or error response for '{question}': {error_text}")
        return {
            "query": question,
            "confidence": 0,
            "handoff": False,
            "reason": "non_json",
            "citations_count": 0,
            "passed": False,
        }

    confidence = _confidence_pct(body)
    handoff = body.get("handoff") is True
    reason = body.get("handoff_reason") or ""
    citations_count = len(body.get("citations", []) or [])
    passed = predicate(body)
    return {
        "query": question,
        "confidence": confidence,
        "handoff": handoff,
        "reason": reason,
        "citations_count": citations_count,
        "passed": passed,
    }


def main() -> int:
    cases: List[Dict[str, object]] = []
    all_passed = True

    baseline_metrics, baseline_error = _get_metrics()
    if baseline_metrics is None:
        print(f"Non-JSON or error response for baseline /metrics: {baseline_error}")
        all_passed = False

    cases.append(
        run_case(
            "ما أفضل هاتف في 2026؟",
            lambda body: (
                _confidence_pct(body) <= 30
                or _contains(str(body.get("answer", "")), "خارج نطاق")
                or body.get("handoff") is True
            ),
        )
    )

    cases.append(
        run_case(
            "عندي مشكلة",
            lambda body: (
                body.get("handoff") is False
                and _confidence_pct(body) == 50
                and len(body.get("citations", []) or []) == 0
                and _clarification_requested(str(body.get("answer", "")))
            ),
        )
    )

    cases.append(
        run_case(
            "كم سعر باقة 55 جيجا؟",
            lambda body: (
                len(body.get("citations", []) or []) >= 1
                or _confidence_pct(body) >= 60
            ),
        )
    )

    cases.append(
        run_case(
            "ما رسوم نقل الملكية؟",
            lambda body: (
                body.get("handoff") is True
                or _confidence_pct(body) == 20
                or len(body.get("citations", []) or []) == 0
            ),
        )
    )

    cases.append(
        run_case(
            "تعرضت لاحتيال وسحب رصيد",
            lambda body: (
                body.get("category") == "fraud" or body.get("handoff") is True
            ),
        )
    )

    cases.append(
        run_case(
            "ما مدة نقل الرقم؟",
            lambda body: (
                body.get("category") == "porting" or _confidence_pct(body) >= 60
            ),
        )
    )

    header = "query | confidence | handoff | reason | citations | status"
    print(header)
    print("-" * len(header))

    for case in cases:
        status = "PASS" if case["passed"] else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(
            f"{case['query']} | {case['confidence']} | {case['handoff']} | "
            f"{case['reason']} | {case['citations_count']} | {status}"
        )

    after_metrics, after_error = _get_metrics()
    if after_metrics is None:
        print(f"Non-JSON or error response for /metrics: {after_error}")
        all_passed = False
    elif baseline_metrics is not None:
        baseline_requests = _sum_counters(baseline_metrics, "query_requests_total")
        baseline_latency = _sum_latency_count(baseline_metrics, "query_latency_ms")
        after_requests = _sum_counters(after_metrics, "query_requests_total")
        after_latency = _sum_latency_count(after_metrics, "query_latency_ms")
        executed = len(cases)
        if (after_requests - baseline_requests) < executed:
            print("Metrics check failed: query_requests_total did not increase as expected.")
            print(after_metrics)
            all_passed = False
        if (after_latency - baseline_latency) < executed:
            print("Metrics check failed: query_latency_ms count did not increase as expected.")
            print(after_metrics)
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
