"""
FitAI - 高级限流模块
Phase 4: 暴力破解防护与限流
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from functools import wraps
from fastapi import Request, HTTPException, status
import hashlib
import json

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.settings import settings


class RateLimitBackend:
    """限流后端接口"""
    
    def get(self, key: str) -> Optional[int]:
        """获取当前计数"""
        raise NotImplementedError
    
    def increment(self, key: str, ttl: int) -> int:
        """增加计数并设置过期时间"""
        raise NotImplementedError
    
    def reset(self, key: str) -> None:
        """重置计数"""
        raise NotImplementedError


class MemoryRateLimitBackend(RateLimitBackend):
    """内存限流后端（用于开发测试）"""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[int, datetime]] = {}
    
    def _cleanup(self):
        """清理过期的键"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, expire_at) in self._cache.items()
            if expire_at <= now
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get(self, key: str) -> Optional[int]:
        self._cleanup()
        if key in self._cache:
            count, _ = self._cache[key]
            return count
        return None
    
    def increment(self, key: str, ttl: int) -> int:
        self._cleanup()
        now = datetime.utcnow()
        
        if key in self._cache:
            count, expire_at = self._cache[key]
            new_count = count + 1
            self._cache[key] = (new_count, expire_at)
        else:
            new_count = 1
            self._cache[key] = (new_count, now + timedelta(seconds=ttl))
        
        return new_count
    
    def reset(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]


class RedisRateLimitBackend(RateLimitBackend):
    """Redis限流后端（用于生产环境）"""
    
    def __init__(self, redis_url: Optional[str] = None):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is not available. Install with: pip install redis")
        
        self.redis_client = redis.from_url(
            redis_url or settings.redis_url,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[int]:
        value = self.redis_client.get(key)
        return int(value) if value is not None else None
    
    def increment(self, key: str, ttl: int) -> int:
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        result = pipe.execute()
        return int(result[0])
    
    def reset(self, key: str) -> None:
        self.redis_client.delete(key)


class RateLimiter:
    """高级限流器"""
    
    # 限流策略配置
    RATE_LIMITS = {
        # 登录接口: 每分钟最多10次
        "login": {
            "max_requests": 10,
            "window_seconds": 60
        },
        # 注册接口: 每小时最多5次
        "register": {
            "max_requests": 5,
            "window_seconds": 3600
        },
        # 普通API: 每分钟最多100次
        "api": {
            "max_requests": 100,
            "window_seconds": 60
        },
        # 敏感操作: 每分钟最多10次
        "sensitive": {
            "max_requests": 10,
            "window_seconds": 60
        }
    }
    
    def __init__(self, backend: Optional[RateLimitBackend] = None):
        if backend:
            self.backend = backend
        elif REDIS_AVAILABLE:
            try:
                self.backend = RedisRateLimitBackend()
            except Exception:
                self.backend = MemoryRateLimitBackend()
        else:
            self.backend = MemoryRateLimitBackend()
    
    @staticmethod
    def get_client_identifier(request: Request) -> str:
        """获取客户端唯一标识（IP + User-Agent哈希）"""
        ip = RateLimiter._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # 创建一个安全的标识符
        identifier = f"{ip}:{user_agent}"
        return hashlib.sha256(identifier.encode()).hexdigest()
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """获取客户端真实IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip
        
        return request.client.host if request.client else "unknown"
    
    def check_rate_limit(
        self,
        limit_type: str,
        identifier: str,
        custom_max: Optional[int] = None,
        custom_window: Optional[int] = None
    ) -> Tuple[bool, int, int]:
        """
        检查是否超过限流
        
        Returns:
            (是否允许, 剩余次数, 重置时间秒数)
        """
        config = self.RATE_LIMITS.get(limit_type, self.RATE_LIMITS["api"])
        max_requests = custom_max or config["max_requests"]
        window_seconds = custom_window or config["window_seconds"]
        
        key = f"rate_limit:{limit_type}:{identifier}"
        current = self.backend.increment(key, window_seconds)
        
        remaining = max(0, max_requests - current)
        reset_at = window_seconds
        
        return current <= max_requests, remaining, reset_at
    
    def reset_limit(self, limit_type: str, identifier: str) -> None:
        """重置限流计数"""
        key = f"rate_limit:{limit_type}:{identifier}"
        self.backend.reset(key)


class BruteForceProtection:
    """暴力破解防护"""
    
    # 配置
    MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数
    USER_LOCKOUT_DURATION = 1800  # 用户锁定时间（秒）= 30分钟
    IP_LOCKOUT_DURATION = 3600  # IP锁定时间（秒）= 1小时
    MAX_IP_ATTEMPTS = 20  # IP最大尝试次数
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    def check_login_attempt(
        self,
        username: str,
        ip: str
    ) -> Tuple[bool, Optional[str], int]:
        """
        检查登录尝试
        
        Returns:
            (是否允许, 锁定原因, 剩余锁定时间秒数)
        """
        # 1. 检查IP是否被锁定
        ip_key = f"login_ip:{ip}"
        ip_allowed, _, ip_reset = self.rate_limiter.check_rate_limit(
            "login",
            ip_key,
            custom_max=self.MAX_IP_ATTEMPTS,
            custom_window=self.IP_LOCKOUT_DURATION
        )
        
        if not ip_allowed:
            return False, "IP地址已被临时锁定，请稍后再试", ip_reset
        
        # 2. 检查用户名是否被锁定
        user_key = f"login_user:{username}"
        user_allowed, _, user_reset = self.rate_limiter.check_rate_limit(
            "login",
            user_key,
            custom_max=self.MAX_LOGIN_ATTEMPTS,
            custom_window=self.USER_LOCKOUT_DURATION
        )
        
        if not user_allowed:
            return False, "账户已被临时锁定，请稍后再试", user_reset
        
        return True, None, 0
    
    def record_failed_attempt(self, username: str, ip: str) -> None:
        """记录失败的登录尝试"""
        # 增加IP计数
        ip_key = f"login_ip:{ip}"
        self.rate_limiter.check_rate_limit(
            "login",
            ip_key,
            custom_max=self.MAX_IP_ATTEMPTS,
            custom_window=self.IP_LOCKOUT_DURATION
        )
        
        # 增加用户名计数
        user_key = f"login_user:{username}"
        self.rate_limiter.check_rate_limit(
            "login",
            user_key,
            custom_max=self.MAX_LOGIN_ATTEMPTS,
            custom_window=self.USER_LOCKOUT_DURATION
        )
    
    def record_successful_login(self, username: str, ip: str) -> None:
        """登录成功后清除计数"""
        ip_key = f"login_ip:{ip}"
        user_key = f"login_user:{username}"
        self.rate_limiter.reset_limit("login", ip_key)
        self.rate_limiter.reset_limit("login", user_key)


# 全局实例
_rate_limiter: Optional[RateLimiter] = None
_brute_force_protection: Optional[BruteForceProtection] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_brute_force_protection() -> BruteForceProtection:
    """获取全局暴力破解防护实例"""
    global _brute_force_protection
    if _brute_force_protection is None:
        _brute_force_protection = BruteForceProtection(get_rate_limiter())
    return _brute_force_protection


def rate_limit(limit_type: str = "api"):
    """
    限流装饰器
    
    用法:
        @app.post("/login")
        @rate_limit("login")
        async def login():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            limiter = get_rate_limiter()
            identifier = RateLimiter.get_client_identifier(request)
            
            allowed, remaining, reset_at = limiter.check_rate_limit(
                limit_type,
                identifier
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Too many requests",
                        "message": "请求过于频繁，请稍后再试",
                        "retry_after": reset_at
                    },
                    headers={"Retry-After": str(reset_at)}
                )
            
            # 将限流信息添加到请求状态
            request.state.rate_limit_remaining = remaining
            request.state.rate_limit_reset = reset_at
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
