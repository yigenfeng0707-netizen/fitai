"""
速率限制中间件
- 通用 API: 100 请求/分钟/IP
- 认证端点: 5 请求/分钟/IP
"""
import time
from collections import defaultdict
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# ── 限流规则 ──
AUTH_PATH_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/mini/auth/",
)

GENERAL_LIMIT = 100       # 请求/分钟
AUTH_LIMIT = 5            # 请求/分钟
WINDOW_SECONDS = 60       # 滑动窗口（秒）
PRUNE_INTERVAL = 120      # 清理间隔（秒）

# ── 内存存储: {ip: {endpoint_prefix: [(timestamp, ...)]}} ──
_requests: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
_last_prune: float = 0.0


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP（支持代理头）"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


def _classify_path(path: str) -> str:
    """将路径归类到通用或认证限流桶"""
    for prefix in AUTH_PATH_PREFIXES:
        if path.startswith(prefix):
            return "auth"
    return "general"


def _prune_stale(now: float) -> None:
    """清理过期记录，防止内存泄漏"""
    global _last_prune
    if now - _last_prune < PRUNE_INTERVAL:
        return
    _last_prune = now
    cutoff = now - WINDOW_SECONDS
    for ip in list(_requests.keys()):
        for bucket in list(_requests[ip].keys()):
            _requests[ip][bucket] = [
                ts for ts in _requests[ip][bucket] if ts > cutoff
            ]
        if not any(_requests[ip].values()):
            del _requests[ip]


def is_rate_limited(ip: str, path: str) -> Optional[int]:
    """
    检查是否被限流。
    返回 None 表示通过，返回 int 表示剩余秒数（需等待）。
    """
    now = time.monotonic()
    _prune_stale(now)
    cutoff = now - WINDOW_SECONDS

    bucket = _classify_path(path)
    limit = AUTH_LIMIT if bucket == "auth" else GENERAL_LIMIT

    timestamps = _requests[ip][bucket]
    # 只保留窗口内的记录
    _requests[ip][bucket] = timestamps = [ts for ts in timestamps if ts > cutoff]

    if len(timestamps) >= limit:
        # 计算需要等待的秒数
        wait = timestamps[0] - cutoff
        return int(wait) + 1
    return None


def record_request(ip: str, path: str) -> None:
    """记录一次请求"""
    bucket = _classify_path(path)
    _requests[ip][bucket].append(time.monotonic())


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 跳过健康检查和 OpenAPI 文档
        if request.url.path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        ip = _get_client_ip(request)
        path = request.url.path

        wait = is_rate_limited(ip, path)
        if wait is not None:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "请求过于频繁，请稍后再试",
                    "code": "rate_limited",
                    "retry_after": wait,
                },
                headers={"Retry-After": str(wait)},
            )

        record_request(ip, path)
        return await call_next(request)
