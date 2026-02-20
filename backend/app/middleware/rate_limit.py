from __future__ import annotations

import os
import time
import json
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, DefaultDict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core import sanitizer
from app.services.query_cache import NEGATIVE_CACHE, POSITIVE_CACHE, build_cache_key


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        max_requests: int = 30,
        window_seconds: int = 60,
        burst_max_requests: int = 10,
        burst_window_seconds: int = 10,
        cache_max_requests: int = 60,
        bypass_paths: Tuple[str, ...] = ("/health", "/metrics"),
    ) -> None:
        super().__init__(app)
        self._max_requests = max_requests
        self._cache_max_requests = cache_max_requests
        self._window_seconds = window_seconds
        self._burst_max_requests = burst_max_requests
        self._burst_window_seconds = burst_window_seconds
        self._bypass_paths = bypass_paths
        self._lock = Lock()
        self._requests: DefaultDict[str, Deque[float]] = defaultdict(
            lambda: deque()
        )
        self._burst_requests: DefaultDict[str, Deque[float]] = defaultdict(
            lambda: deque()
        )
        self._cached_requests: DefaultDict[str, Deque[float]] = defaultdict(
            lambda: deque()
        )

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _key(self, request: Request, channel: str, locale: str) -> str:
        client = self._client_ip(request)
        return f"{client}|{channel}|{locale}"

    def _rate_limited(self, retry_after: int) -> JSONResponse:
        headers = {"Retry-After": str(max(1, retry_after))}
        return JSONResponse(
            status_code=429,
            content={
                "error_code": "rate_limited",
                "retry_after_seconds": max(1, retry_after),
            },
            headers=headers,
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        if os.getenv("APP_ENV") == "test" or os.getenv("DISABLE_RATE_LIMIT") == "1":
            return await call_next(request)

        if request.url.path in self._bypass_paths:
            return await call_next(request)

        channel = request.headers.get("X-Channel", "unknown")
        locale = request.headers.get("X-Locale", "unknown")
        cache_hit = False
        if request.url.path == "/query" and request.method.upper() == "POST":
            body = await request.body()
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except ValueError:
                payload = {}
            question = str(payload.get("question", ""))
            locale = str(payload.get("locale", locale or "ar-SA"))
            channel = str(payload.get("channel", channel))
            if question:
                masked_question, _, _ = sanitizer.sanitize_question(question)
                cache_key = build_cache_key(masked_question, locale, channel)
                if POSITIVE_CACHE.get(cache_key) or NEGATIVE_CACHE.get(cache_key):
                    cache_hit = True

            async def receive() -> dict:
                return {"type": "http.request", "body": body, "more_body": False}

            request = Request(request.scope, receive)

        now = time.time()
        key = self._key(request, channel, locale or "unknown")
        with self._lock:
            if cache_hit:
                cached_bucket = self._cached_requests[key]
                while cached_bucket and now - cached_bucket[0] > self._window_seconds:
                    cached_bucket.popleft()
                if len(cached_bucket) < self._cache_max_requests:
                    cached_bucket.append(now)
                    return await call_next(request)

            burst_bucket = self._burst_requests[key]
            while burst_bucket and now - burst_bucket[0] > self._burst_window_seconds:
                burst_bucket.popleft()
            if len(burst_bucket) >= self._burst_max_requests:
                retry_after = int(self._burst_window_seconds - (now - burst_bucket[0]))
                return self._rate_limited(retry_after)

            bucket = self._requests[key]
            while bucket and now - bucket[0] > self._window_seconds:
                bucket.popleft()
            if len(bucket) >= self._max_requests:
                retry_after = int(self._window_seconds - (now - bucket[0]))
                return self._rate_limited(retry_after)
            burst_bucket.append(now)
            bucket.append(now)

        return await call_next(request)
