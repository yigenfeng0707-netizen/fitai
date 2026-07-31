"""
错误追踪中间件
"""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from backend.logger import logger


class ErrorTrackerMiddleware(BaseHTTPMiddleware):
    """追踪未处理异常的中间件"""

    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.exception(
                "Unhandled exception [req=%s] %s %s: %s",
                request_id, request.method, request.url.path, str(exc),
            )
            raise
