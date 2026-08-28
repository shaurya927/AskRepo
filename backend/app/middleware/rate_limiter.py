"""Rate limiter middleware — IP-based sliding window rate limiting."""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class _Window:
    """Sliding window counter."""
    timestamps: list[float] = field(default_factory=list)

    def count_in_window(self, window_seconds: float) -> int:
        now = time.time()
        cutoff = now - window_seconds
        self.timestamps = [t for t in self.timestamps if t > cutoff]
        return len(self.timestamps)

    def add(self):
        self.timestamps.append(time.time())

    def seconds_until_next(self, window_seconds: float) -> int:
        if not self.timestamps:
            return 0
        oldest = min(self.timestamps)
        return max(0, int(oldest + window_seconds - time.time()))


class RateLimiter(BaseHTTPMiddleware):
    """IP-based rate limiter for analysis and AI chat endpoints."""

    WINDOW = 86400  # 24 hours in seconds

    def __init__(self, app, max_analyses: int = 3, max_ai_requests: int = 20):
        super().__init__(app)
        self.max_analyses = max_analyses
        self.max_ai_requests = max_ai_requests
        # IP -> endpoint category -> window
        self._limits: dict[str, dict[str, _Window]] = defaultdict(lambda: defaultdict(_Window))

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method

        # Check analysis rate limit (POST to /api/repositories)
        if method == "POST" and path == "/api/repositories":
            window = self._limits[client_ip]["analysis"]
            count = window.count_in_window(self.WINDOW)
            if count >= self.max_analyses:
                retry_after = window.seconds_until_next(self.WINDOW)
                logger.warning("Rate limited (analysis): IP=%s, count=%d", client_ip, count)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": f"Analysis limit reached ({self.max_analyses}/day). Try again later.",
                            "detail": f"Retry after {retry_after // 3600} hours.",
                            "status": 429,
                        }
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            window.add()

        # Check AI chat rate limit (POST to chat endpoints)
        if method == "POST" and ("/chat" in path and "/repositories/" in path):
            window = self._limits[client_ip]["ai_chat"]
            count = window.count_in_window(self.WINDOW)
            if count >= self.max_ai_requests:
                retry_after = window.seconds_until_next(self.WINDOW)
                logger.warning("Rate limited (AI chat): IP=%s, count=%d", client_ip, count)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": f"AI chat limit reached ({self.max_ai_requests}/day). Try again later.",
                            "detail": f"Retry after {retry_after // 3600} hours.",
                            "status": 429,
                        }
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            window.add()

        response = await call_next(request)
        
        # Inject rate limit headers for AI chat
        if method == "POST" and ("/chat" in path and "/repositories/" in path):
            window = self._limits[client_ip]["ai_chat"]
            count = window.count_in_window(self.WINDOW)
            remaining = max(0, self.max_ai_requests - count)
            response.headers["X-RateLimit-Limit"] = str(self.max_ai_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(window.seconds_until_next(self.WINDOW))

        return response
