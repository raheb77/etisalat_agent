import json
from pathlib import Path

import requests

API_URL = "http://127.0.0.1:8001/query"
TEST_SET = Path("eval/test_set.jsonl")
OUT_FILE = Path("eval/results.jsonl")


def classify_result(body: dict) -> str:
    if body.get("handoff") is True:
        return "handoff"

    answer = (body.get("answer") or "").strip()

    insufficiency_markers = [
        "لم نجد معلومات محددة",
        "لا توجد معلومات",
        "لا تتضمن",
        "لا تحتوي",
        "خارج نطاق",
    ]
    if any(marker in answer for marker in insufficiency_markers):
        return "reject_or_insufficient"

    return "correct_answer"


def main() -> None:
    rows = []

    for line in TEST_SET.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        item = json.loads(line)
        payload = {
            "question": item["question"],
            "locale": "ar-SA",
            "channel": "csr_ui",
        }

        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        body = response.json()

        actual = classify_result(body)
        passed = actual == item["expected"]

        row = {
            "question": item["question"],
            "expected": item["expected"],
            "actual": actual,
            "passed": passed,
            "category": body.get("category"),
            "confidence": body.get("confidence"),
            "handoff": body.get("handoff"),
            "answer": body.get("answer"),
        }
        rows.append(row)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    total = len(rows)
    passed = sum(1 for r in rows if r["passed"])
    correct = sum(1 for r in rows if r["actual"] == "correct_answer")
    handoff = sum(1 for r in rows if r["actual"] == "handoff")
    rejects = sum(1 for r in rows if r["actual"] == "reject_or_insufficient")

    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Correct answers: {correct}")
    print(f"Handoffs: {handoff}")
    print(f"Reject / insufficient: {rejects}")
    print(f"Failed expectations: {total - passed}")


if __name__ == "__main__":
    main()