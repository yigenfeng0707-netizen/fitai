"""
FitAI - Phase 4 测试
测试暴力破解防护与限流
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.auth.rate_limit import (
    RateLimiter,
    MemoryRateLimitBackend,
    BruteForceProtection,
    get_rate_limiter,
    get_brute_force_protection
)


class TestMemoryRateLimitBackend:
    """内存后端测试"""
    
    def test_increment_and_get(self):
        """测试增加和获取计数"""
        backend = MemoryRateLimitBackend()
        
        # 第一次增加
        count = backend.increment("test_key", 60)
        assert count == 1
        
        # 第二次增加
        count = backend.increment("test_key", 60)
        assert count == 2
        
        # 获取当前计数
        current = backend.get("test_key")
        assert current == 2
    
    def test_reset(self):
        """测试重置"""
        backend = MemoryRateLimitBackend()
        backend.increment("test_key", 60)
        
        backend.reset("test_key")
        assert backend.get("test_key") is None
    
    def test_cleanup_expired(self):
        """测试过期清理"""
        backend = MemoryRateLimitBackend()
        backend.increment("test_key", 1)  # 1秒过期
        
        # 强制修改内部状态来测试
        with patch.object(backend, '_cache', new={}):
            expire_time = datetime.utcnow() - timedelta(seconds=2)
            backend._cache["test_key"] = (5, expire_time)
            
            # 清理应该移除过期键
            backend._cleanup()
            assert "test_key" not in backend._cache


class TestRateLimiter:
    """限流器测试"""
    
    def test_check_rate_limit_allowed(self):
        """测试在限流内的请求"""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend)
        
        allowed, remaining, reset = limiter.check_rate_limit(
            "api",
            "test_client",
            custom_max=5,
            custom_window=60
        )
        
        assert allowed is True
        assert remaining == 4
    
    def test_check_rate_limit_exceeded(self):
        """测试超过限流"""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend)
        
        # 先消耗完次数
        for i in range(5):
            limiter.check_rate_limit(
                "api",
                "test_client",
                custom_max=5,
                custom_window=60
            )
        
        # 第6次应该被拒绝
        allowed, remaining, reset = limiter.check_rate_limit(
            "api",
            "test_client",
            custom_max=5,
            custom_window=60
        )
        
        assert allowed is False
        assert remaining == 0
    
    def test_reset_limit(self):
        """测试重置限流"""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend)
        
        limiter.check_rate_limit("api", "test_client", custom_max=5)
        limiter.reset_limit("api", "test_client")
        
        # 重置后应该可以再次请求
        allowed, remaining, _ = limiter.check_rate_limit(
            "api",
            "test_client",
            custom_max=5
        )
        assert allowed is True
        assert remaining == 4
    
    def test_get_client_identifier(self):
        """测试获取客户端标识"""
        mock_request = Mock()
        mock_request.headers = {"User-Agent": "TestAgent"}
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        
        identifier = RateLimiter.get_client_identifier(mock_request)
        assert identifier is not None
        assert len(identifier) == 64  # SHA256长度


class TestBruteForceProtection:
    """暴力破解防护测试"""
    
    def test_check_login_allowed_initially(self):
        """测试初始状态允许登录"""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend)
        protection = BruteForceProtection(limiter)
        
        allowed, reason, _ = protection.check_login_attempt("test_user", "192.168.1.1")
        assert allowed is True
        assert reason is None
    
    def test_user_lockout_after_multiple_failures(self):
        """测试多次失败后用户锁定"""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend)
        protection = BruteForceProtection(limiter)
        
        # 设置较低的阈值便于测试
        protection.MAX_LOGIN_ATTEMPTS = 3
        protection.USER_LOCKOUT_DURATION = 60
        
        # 失败3次
        for i in range(3):
            protection.record_failed_attempt("test_user", "192.168.1.1")
        
        # 第4次应该被拒绝
        allowed, reason, _ = protection.check_login_attempt("test_user", "192.168.1.1")
        assert allowed is False
        assert "账户已被临时锁定" in reason
    
    def test_ip_lockout_after_multiple_failures(self):
        """测试多次失败后IP锁定"""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend)
        protection = BruteForceProtection(limiter)
        
        # 设置较低的阈值便于测试
        protection.MAX_IP_ATTEMPTS = 3
        protection.IP_LOCKOUT_DURATION = 60
        
        # 从同一IP失败3次（不同用户名）
        for i in range(3):
            protection.record_failed_attempt(f"user_{i}", "192.168.1.1")
        
        # 第4次应该被拒绝
        allowed, reason, _ = protection.check_login_attempt("new_user", "192.168.1.1")
        assert allowed is False
        assert "IP地址已被临时锁定" in reason
    
    def test_successful_login_resets_counts(self):
        """测试成功登录重置计数"""
        backend = MemoryRateLimitBackend()
        limiter = RateLimiter(backend)
        protection = BruteForceProtection(limiter)
        
        # 记录几次失败
        for i in range(2):
            protection.record_failed_attempt("test_user", "192.168.1.1")
        
        # 成功登录
        protection.record_successful_login("test_user", "192.168.1.1")
        
        # 应该仍然可以继续登录
        allowed, reason, _ = protection.check_login_attempt("test_user", "192.168.1.1")
        assert allowed is True


class TestGlobalInstances:
    """全局实例测试"""
    
    def test_get_rate_limiter(self):
        """测试获取全局限流器"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
    
    def test_get_brute_force_protection(self):
        """测试获取全局暴力破解防护"""
        protection1 = get_brute_force_protection()
        protection2 = get_brute_force_protection()
        
        assert protection1 is protection2


class TestRateLimitPolicies:
    """限流策略测试"""
    
    def test_login_policy_exists(self):
        """测试登录策略存在"""
        limiter = RateLimiter(MemoryRateLimitBackend())
        assert "login" in limiter.RATE_LIMITS
    
    def test_api_policy_exists(self):
        """测试API策略存在"""
        limiter = RateLimiter(MemoryRateLimitBackend())
        assert "api" in limiter.RATE_LIMITS
    
    def test_sensitive_policy_exists(self):
        """测试敏感操作策略存在"""
        limiter = RateLimiter(MemoryRateLimitBackend())
        assert "sensitive" in limiter.RATE_LIMITS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
