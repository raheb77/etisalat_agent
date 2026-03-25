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
    {"question":"ما مدة نقل الرقم؟","expected":"correct_answer","expected_category":"porting","notes":"should answer with 3 ساعات عمل"}
{"question":"كم أقصى مدة قانونية لنقل رقم الجوال؟","expected":"correct_answer","expected_category":"porting","notes":"should answer with 3 ساعات عمل"}
{"question":"إذا كان الرقم عالقًا بين الشبكتين، كم أنتظر قبل التصعيد؟","expected":"correct_answer","expected_category":"porting","notes":"should answer with ساعتان عمل"}
{"question":"كم يستغرق نقل الهاتف المتنقل؟","expected":"correct_answer","expected_category":"porting","notes":"should mention 30 دقيقة للموافقة + 15 دقيقة للتفعيل"}
{"question":"كم يستغرق نقل الهاتف الثابت؟","expected":"correct_answer","expected_category":"porting","notes":"should answer with ساعتان للموافقة + 7 أيام للتفعيل"}
{"question":"كم سعر باقة مفوتر فليكس؟","expected":"correct_answer","expected_category":"plans","notes":"should answer with 370 ريال أو 335 عرض"}
{"question":"كم سعر باقة مفوتر 4؟","expected":"correct_answer","expected_category":"plans","notes":"should answer with 517.5 ريال أو 423 عرض"}
{"question":"كم سعر سوا لايك بلس؟","expected":"correct_answer","expected_category":"plans","notes":"should answer with 86.25 ريال"}
{"question":"كم سعر سوا بيسك؟","expected":"correct_answer","expected_category":"plans","notes":"should answer with 34.5 ريال"}
{"question":"كم رسوم التحويل من مفوتر إلى سوا؟","expected":"correct_answer","expected_category":"plans","notes":"should answer with 50 ريال"}
{"question":"خلال كم يوم يجب سداد المستحقات عند التحويل من مفوتر إلى سوا؟","expected":"correct_answer","expected_category":"plans","notes":"should answer with 5 أيام"}
{"question":"كم رسوم بدل فاقد الشريحة لنفس الرقم؟","expected":"correct_answer","expected_category":"billing","notes":"should answer with 25 ريال"}
{"question":"ما رقم خدمة العملاء للأفراد؟","expected":"correct_answer","expected_category":"support","notes":"should answer with 900"}
{"question":"ما رقم خدمة قطاع الأعمال؟","expected":"correct_answer","expected_category":"support","notes":"should answer with 909"}
{"question":"ما رقم stc من خارج المملكة؟","expected":"correct_answer","expected_category":"support","notes":"should answer with +966114555555"}
{"question":"إلى متى يمكن تصعيد الشكوى إلى الهيئة بعد إغلاقها؟","expected":"correct_answer","expected_category":"complaints","notes":"should answer with 180 يوم"}
{"question":"ما الخطوات المطلوبة لتقديم شكوى رسمية؟","expected":"reject_or_insufficient","expected_category":"complaints","notes":"facts include escalation window, not full complaint steps"}
{"question":"ما المستندات المطلوبة لنقل الرقم؟","expected":"reject_or_insufficient","expected_category":"porting","notes":"facts include timing and launch date, not required documents"}
{"question":"أريد تفسيرًا قانونيًا لحق الشركة في رفض نقل الرقم","expected":"handoff","expected_category":"legal","notes":"should escalate as legal interpretation request"}
{"question":"تم سحب رصيدي بسبب اشتراك تلقائي وأريد تصعيدًا عاجلًا","expected":"handoff","expected_category":"fraud","notes":"should escalate as high-risk complaint/fraud-like case"}