"""Usage tracker middleware — logs API requests to DB asynchronously."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import request_id_var

logger = logging.getLogger(__name__)


class UsageTracker(BaseHTTPMiddleware):
    """Logs every API request to the usage_logs table (fire-and-forget)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Set request ID for structured logging
        rid = str(uuid.uuid4())[:8]
        request_id_var.set(rid)

        start = time.time()
        response = await call_next(request)
        elapsed_ms = int((time.time() - start) * 1000)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method

        # Only log API requests (skip docs, static, etc.)
        if path.startswith("/api/"):
            logger.info(
                "%s %s → %d (%dms) [IP: %s]",
                method, path, response.status_code, elapsed_ms, client_ip,
            )

            # Fire-and-forget DB insert (don't block the response)
            try:
                from app.core.database import async_session_factory
                from app.models.usage_log import UsageLog
                import hashlib

                hashed_ip = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

                async def _log():
                    try:
                        async with async_session_factory() as session:
                            log = UsageLog(
                                client_ip=hashed_ip,
                                endpoint=path,
                                method=method,
                                status_code=response.status_code,
                                response_time_ms=elapsed_ms,
                            )
                            session.add(log)
                            await session.commit()
                    except Exception:
                        pass  # Never fail the request for logging

                import asyncio
                asyncio.create_task(_log())
            except Exception:
                pass  # Silently ignore logging failures

        return response
