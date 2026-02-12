import json
import os
import time
from hashlib import sha256
from pathlib import Path
from typing import Dict


def _audit_log_path() -> Path:
    base = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return base / ".audit" / "audit.log"


def _hash_question(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()[:12]


def log_event(event: Dict[str, object]) -> None:
    event = dict(event)
    event.setdefault("timestamp", time.time())

    sanitized_question = event.pop("sanitized_question", "")
    if sanitized_question:
        event["question_hash"] = _hash_question(sanitized_question)

    if "question" in event:
        event.pop("question")

    log_path = _audit_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
