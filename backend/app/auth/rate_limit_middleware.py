"""
FitAI - 限流中间件
Phase 4: 暴力破解防护与限流
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Set
import re

from app.auth.rate_limit import (
    get_rate_limiter,
    RateLimiter
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    全局限流中间件
    
    自动对API请求进行限流保护
    """
    
    # 不需要限流的路径
    EXCLUDE_PATHS: Set[str] = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico"
    }
    
    # 路径限流规则
    PATH_RULES = [
        # 登录相关
        (re.compile(r"^/api/v1/auth/login$"), "login"),
        (re.compile(r"^/api/v1/auth/register$"), "register"),
        # 敏感操作
        (re.compile(r"^/api/v1/system/.*$"), "sensitive"),
        (re.compile(r"^/api/v1/finance/.*$"), "sensitive"),
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        
        # 1. 检查是否是排除路径
        if self._is_excluded(path):
            return await call_next(request)
        
        # 2. 确定限流类型
        limit_type = self._get_limit_type(path)
        
        # 3. 检查限流
        limiter = get_rate_limiter()
        identifier = RateLimiter.get_client_identifier(request)
        
        allowed, remaining, reset_at = limiter.check_rate_limit(
            limit_type,
            identifier
        )
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": reset_at,
                    "limit_type": limit_type
                },
                headers={
                    "Retry-After": str(reset_at),
                    "X-RateLimit-Limit": str(limiter.RATE_LIMITS[limit_type]["max_requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at)
                }
            )
        
        # 4. 添加限流响应头
        response = await call_next(request)
        
        config = limiter.RATE_LIMITS.get(limit_type, limiter.RATE_LIMITS["api"])
        response.headers["X-RateLimit-Limit"] = str(config["max_requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        
        return response
    
    def _is_excluded(self, path: str) -> bool:
        """检查是否是排除路径"""
        if path in self.EXCLUDE_PATHS:
            return True
        
        # 检查前缀
        excluded_prefixes = ["/docs", "/openapi", "/static"]
        for prefix in excluded_prefixes:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _get_limit_type(self, path: str) -> str:
        """根据路径确定限流类型"""
        for pattern, limit_type in self.PATH_RULES:
            if pattern.match(path):
                return limit_type
        return "api"
