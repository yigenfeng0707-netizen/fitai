"""
请求日志中间件
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from backend.config import settings
from backend.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录请求日志的中间件"""

    async def dispatch(self, request, call_next):
        if not settings.LOG_REQUEST_ENABLED:
            return await call_next(request)

        start = time.time()
        method = request.method
        path = request.url.path

        response = await call_next(request)

        duration = time.time() - start
        status_code = response.status_code

        log_msg = f"{method} {path} -> {status_code} ({duration:.3f}s)"

        if duration > settings.SLOW_REQUEST_THRESHOLD:
            logger.warning(f"SLOW REQUEST: {log_msg}")
        elif status_code >= 500:
            logger.error(f"ERROR RESPONSE: {log_msg}")
        elif status_code >= 400:
            logger.warning(f"CLIENT ERROR: {log_msg}")
        else:
            logger.info(log_msg)

        return response
