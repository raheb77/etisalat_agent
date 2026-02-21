from __future__ import annotations

import time


class StageTimer:
    def __init__(self) -> None:
        self._start: float | None = None
        self.duration_ms: int = 0

    def __enter__(self) -> "StageTimer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._start is None:
            self.duration_ms = 0
        else:
            self.duration_ms = int((time.perf_counter() - self._start) * 1000)
        return False
