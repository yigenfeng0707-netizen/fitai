"""
速率限制中间件 - Redis 版本
支持多 worker/容器部署
- 通用 API: 100 请求/分钟/IP
- 认证端点: 5 请求/分钟/IP
"""
import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.config import settings

# ── 限流规则 ──
AUTH_PATH_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/mini/auth/",
)

GENERAL_LIMIT = 100       # 请求/分钟
AUTH_LIMIT = 5            # 请求/分钟
WINDOW_SECONDS = 60       # 滑动窗口（秒）

# ── Redis 连接 ──
_redis_client = None


def _get_redis():
    """获取 Redis 客户端（延迟初始化）"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            redis_url = settings.REDIS_URL or "redis://localhost:6379/1"
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            _redis_client.ping()
        except Exception:
            # Redis 不可用时降级为内存模式
            _redis_client = False
            return None
    return _redis_client if _redis_client is not False else None


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


# ── 内存降级存储 ──
_memory_store: dict[str, dict[str, list[float]]] = {}


def _is_rate_limited_memory(ip: str, path: str) -> Optional[int]:
    """内存模式限流检查"""
    from collections import defaultdict
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS

    bucket = _classify_path(path)
    limit = AUTH_LIMIT if bucket == "auth" else GENERAL_LIMIT

    if ip not in _memory_store:
        _memory_store[ip] = {}
    if bucket not in _memory_store[ip]:
        _memory_store[ip][bucket] = []

    timestamps = _memory_store[ip][bucket]
    _memory_store[ip][bucket] = timestamps = [ts for ts in timestamps if ts > cutoff]

    if len(timestamps) >= limit:
        wait = timestamps[0] - cutoff
        return int(wait) + 1
    return None


def _record_request_memory(ip: str, path: str) -> None:
    """内存模式记录请求"""
    now = time.monotonic()
    bucket = _classify_path(path)
    if ip not in _memory_store:
        _memory_store[ip] = {}
    if bucket not in _memory_store[ip]:
        _memory_store[ip][bucket] = []
    _memory_store[ip][bucket].append(now)


def is_rate_limited(ip: str, path: str) -> Optional[int]:
    """
    检查是否被限流。
    返回 None 表示通过，返回 int 表示剩余秒数（需等待）。
    """
    redis = _get_redis()

    if redis is None:
        return _is_rate_limited_memory(ip, path)

    try:
        bucket = _classify_path(path)
        limit = AUTH_LIMIT if bucket == "auth" else GENERAL_LIMIT
        key = f"ratelimit:{ip}:{bucket}"
        now = time.time()
        cutoff = now - WINDOW_SECONDS

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, WINDOW_SECONDS + 10)
        results = pipe.execute()

        request_count = results[2]

        if request_count >= limit:
            oldest = redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                wait = oldest[0][1] - cutoff
                return int(wait) + 1
        return None
    except Exception:
        return _is_rate_limited_memory(ip, path)


def record_request(ip: str, path: str) -> None:
    """记录一次请求"""
    redis = _get_redis()

    if redis is None:
        _record_request_memory(ip, path)
        return

    try:
        bucket = _classify_path(path)
        key = f"ratelimit:{ip}:{bucket}"
        now = time.time()
        redis.zadd(key, {str(now): now})
        redis.expire(key, WINDOW_SECONDS + 10)
    except Exception:
        _record_request_memory(ip, path)


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
