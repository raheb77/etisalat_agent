from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class DecisionResult:
    response: Dict[str, Any]
    telemetry: Dict[str, Any]
    decision_path: List[str]

    def to_cache(self) -> Dict[str, Any]:
        return {
            "response": copy.deepcopy(self.response),
            "telemetry": copy.deepcopy(self.telemetry),
            "decision_path": list(self.decision_path),
        }

    @classmethod
    def from_cache(cls, payload: Dict[str, Any]) -> "DecisionResult":
        response = copy.deepcopy(payload.get("response", {}))
        telemetry = copy.deepcopy(payload.get("telemetry", {}))
        decision_path = list(payload.get("decision_path", []))
        return cls(response=response, telemetry=telemetry, decision_path=decision_path)
