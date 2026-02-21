from __future__ import annotations

import time
from threading import Lock
from typing import Dict, List


class TTLCache:
    def __init__(self, max_items: int = 256, ttl_seconds: int = 60) -> None:
        self._max_items = max_items
        self._ttl_seconds = ttl_seconds
        self._data: Dict[str, tuple[dict, float]] = {}
        self._order: List[str] = []
        self._lock = Lock()

    def _evict_expired(self, now: float) -> None:
        if not self._order:
            return
        new_order: List[str] = []
        for key in self._order:
            item = self._data.get(key)
            if not item:
                continue
            _, ts = item
            if now - ts > self._ttl_seconds:
                self._data.pop(key, None)
                continue
            new_order.append(key)
        self._order = new_order

    def get(self, key: str) -> dict | None:
        now = time.time()
        with self._lock:
            self._evict_expired(now)
            item = self._data.get(key)
            if not item:
                return None
            value, _ = item
            return value

    def set(self, key: str, value: dict) -> None:
        now = time.time()
        with self._lock:
            self._evict_expired(now)
            if key in self._data:
                self._order = [k for k in self._order if k != key]
            self._data[key] = (value, now)
            self._order.append(key)
            while len(self._data) > self._max_items and self._order:
                oldest = self._order.pop(0)
                self._data.pop(oldest, None)
