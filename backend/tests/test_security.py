"""
安全模块测试
- 速率限制
- 安全头
- 密码策略
- SQL 注入预防
- XSS 预防
- CORS 配置
- JWT Token 过期
- API Key 验证
"""
import time
from unittest.mock import patch, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from backend.core.rate_limiter import (
    RateLimitMiddleware,
    is_rate_limited,
    record_request,
    _requests,
    AUTH_LIMIT,
    GENERAL_LIMIT,
)
from backend.core.security_headers import SecurityHeadersMiddleware
from backend.core.password_policy import (
    validate_password_strength,
    enforce_password_policy,
    PasswordPolicyError,
)
from backend.core.sanitizer import (
    strip_html,
    sanitize_string,
    sanitize_dict,
    is_safe_path,
    check_sql_injection_risk,
)
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    blacklist_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from backend.core.api_key import (
    generate_api_key,
    hash_api_key,
    ApiKeyService,
)


# ── 速率限制测试 ──

class TestRateLimiter:
    """速率限制中间件测试"""

    def setup_method(self):
        """每个测试前清理状态"""
        _requests.clear()

    def test_rate_limiter_blocks_excessive_requests(self):
        """测试：超过限制后返回 429"""
        ip = "192.168.1.1"
        path = "/api/v1/auth/login"

        # 认证端点限制为 5 次/分钟
        for _ in range(AUTH_LIMIT):
            wait = is_rate_limited(ip, path)
            assert wait is None, f"第 {_ + 1} 次请求不应被限流"
            record_request(ip, path)

        # 第 6 次应该被限流
        wait = is_rate_limited(ip, path)
        assert wait is not None, "超过限制后应返回等待时间"

    def test_rate_limiter_general_api(self):
        """测试：通用 API 限流（100 次/分钟）"""
        ip = "192.168.1.2"
        path = "/api/v1/members"

        for _ in range(GENERAL_LIMIT):
            wait = is_rate_limited(ip, path)
            assert wait is None
            record_request(ip, path)

        wait = is_rate_limited(ip, path)
        assert wait is not None, "超过通用限制后应返回等待时间"

    def test_rate_limiter_different_ips_independent(self):
        """测试：不同 IP 的限流计数独立"""
        ip1 = "10.0.0.1"
        ip2 = "10.0.0.2"
        path = "/api/v1/auth/login"

        for _ in range(AUTH_LIMIT):
            record_request(ip1, path)
            record_request(ip2, path)

        # ip1 应被限流
        assert is_rate_limited(ip1, path) is not None
        # ip2 也应被限流（都达到了限制）
        assert is_rate_limited(ip2, path) is not None

    def test_rate_limiter_skips_health_check(self):
        """测试：健康检查端点不限流"""
        ip = "192.168.1.3"
        path = "/health"

        for _ in range(200):
            wait = is_rate_limited(ip, path)
            assert wait is None, "健康检查端点不应被限流"

    def test_rate_limiter_auth_vs_general_separate(self):
        """测试：认证端点和通用端点限流独立"""
        ip = "192.168.1.4"

        # 耗尽认证端点配额
        for _ in range(AUTH_LIMIT):
            record_request(ip, "/api/v1/auth/login")

        assert is_rate_limited(ip, "/api/v1/auth/login") is not None
        # 通用端点应不受影响
        assert is_rate_limited(ip, "/api/v1/members") is None


# ── 安全头测试 ──

class TestSecurityHeaders:
    """安全响应头中间件测试"""

    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        """测试：响应包含所有必要的安全头"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        # 构造模拟请求
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/members",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        async def call_next(req):
            return Response(content="ok")

        response = await middleware.dispatch(request, call_next)

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in response.headers

    @pytest.mark.asyncio
    async def test_api_response_no_cache(self):
        """测试：API 响应包含 no-cache 头"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/stores",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        async def call_next(req):
            return Response(content="ok")

        response = await middleware.dispatch(request, call_next)

        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]

    @pytest.mark.asyncio
    async def test_server_header_removed(self):
        """测试：Server 头被移除"""
        middleware = SecurityHeadersMiddleware(app=MagicMock())

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/members",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        async def call_next(req):
            resp = Response(content="ok")
            resp.headers["Server"] = "uvicorn/1.0.0"
            return resp

        response = await middleware.dispatch(request, call_next)
        assert "Server" not in response.headers


# ── 密码策略测试 ──

class TestPasswordPolicy:
    """密码强度策略测试"""

    def test_password_policy_rejects_weak(self):
        """测试：弱密码被拒绝"""
        weak_passwords = [
            "12345678",       # 纯数字
            "abcdefgh",       # 纯字母
            "Abc123",         # 太短
            "password",       # 常见密码
            "admin123",       # 常见密码
            "aaaaaaaa",       # 重复字符
            "11111111",       # 纯数字
        ]
        for pwd in weak_passwords:
            errors = validate_password_strength(pwd)
            assert len(errors) > 0, f"弱密码 '{pwd}' 应被拒绝"

    def test_password_policy_accepts_strong(self):
        """测试：强密码通过"""
        strong_passwords = [
            "MyP@ssw0rd",
            "Secure123",
            "TestPass99",
            "Abcdefg1",
        ]
        for pwd in strong_passwords:
            errors = validate_password_strength(pwd)
            assert len(errors) == 0, f"强密码 '{pwd}' 应通过: {errors}"

    def test_enforce_password_policy_raises(self):
        """测试：enforce_password_policy 对弱密码抛出异常"""
        with pytest.raises(PasswordPolicyError):
            enforce_password_policy("12345678")

    def test_enforce_password_policy_passes(self):
        """测试：enforce_password_policy 对强密码不抛异常"""
        enforce_password_policy("MyP@ssw0rd")  # 不应抛异常

    def test_password_requires_uppercase(self):
        """测试：必须包含大写字母"""
        errors = validate_password_strength("abcdefg1")
        assert any("大写" in e for e in errors)

    def test_password_requires_lowercase(self):
        """测试：必须包含小写字母"""
        errors = validate_password_strength("ABCDEFG1")
        assert any("小写" in e for e in errors)

    def test_password_requires_number(self):
        """测试：必须包含数字"""
        errors = validate_password_strength("Abcdefgh")
        assert any("数字" in e for e in errors)

    def test_password_rejects_common(self):
        """测试：常见密码被拒绝"""
        errors = validate_password_strength("Password1")
        # "password1" is in common list (case-insensitive check)
        assert any("常见" in e for e in errors)


# ── SQL 注入预防测试 ──

class TestSQLInjectionPrevention:
    """SQL 注入预防测试"""

    def test_sql_injection_prevention(self):
        """测试：检测 SQL 注入模式"""
        malicious_inputs = [
            "1 OR 1=1",
            "1; DROP TABLE users",
            "' OR '1'='1",
            "1 UNION SELECT * FROM users",
            "admin'--",
            "1 AND 1=1",
        ]
        for inp in malicious_inputs:
            assert check_sql_injection_risk(inp), f"应检测到 SQL 注入: {inp}"

    def test_safe_inputs_pass(self):
        """测试：正常输入不被误报"""
        safe_inputs = [
            "张三",
            "hello world",
            "test@example.com",
            "13800138000",
            "2024-01-01",
            "normal text with numbers 123",
        ]
        for inp in safe_inputs:
            assert not check_sql_injection_risk(inp), f"正常输入不应被标记: {inp}"


# ── XSS 预防测试 ──

class TestXSSPrevention:
    """XSS 预防测试"""

    def test_xss_prevention(self):
        """测试：HTML 标签被剥离"""
        malicious = "<script>alert('xss')</script>"
        cleaned = strip_html(malicious)
        assert "<script>" not in cleaned
        assert "alert" in cleaned  # 文本内容保留

    def test_xss_sanitization(self):
        """测试：sanitize_string 转义 HTML"""
        malicious = "<img src=x onerror=alert(1)>"
        sanitized = sanitize_string(malicious)
        assert "<img" not in sanitized
        assert "onerror" not in sanitized

    def test_sanitize_dict(self):
        """测试：字典递归消毒"""
        data = {
            "name": "<b>Test</b>",
            "nested": {"html": "<script>alert(1)</script>"},
            "safe": 123,
        }
        result = sanitize_dict(data)
        assert "<b>" not in result["name"]
        assert "<script>" not in result["nested"]["html"]
        assert result["safe"] == 123

    def test_safe_text_unchanged(self):
        """测试：正常文本不受影响（strip_html 保留纯文本）"""
        text = "Hello, World!"
        # strip_html 应保留纯文本
        assert strip_html(text) == "Hello, World!"
        # sanitize_string 会 escape，但无特殊字符时结果相同
        assert strip_html(text) == text


# ── CORS 配置测试 ──

class TestCORSConfig:
    """CORS 配置测试"""

    def test_cors_restricts_origins(self):
        """测试：CORS 配置限制来源"""
        from backend.config import Settings

        # 非生产环境允许通配符
        dev_settings = Settings(APP_ENV="development", CORS_ORIGINS="*")
        assert dev_settings.CORS_ORIGINS == "*"

        # 指定来源
        prod_settings = Settings(
            APP_ENV="development",
            CORS_ORIGINS="https://app.example.com,https://admin.example.com",
        )
        origins = [o.strip() for o in prod_settings.CORS_ORIGINS.split(",") if o.strip()]
        assert len(origins) == 2
        assert "https://app.example.com" in origins

    def test_cors_production_rejects_wildcard(self):
        """测试：生产环境拒绝通配符 CORS"""
        from pydantic import ValidationError
        from backend.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="a" * 32,
                CORS_ORIGINS="*",
            )
        assert "CORS_ORIGINS" in str(exc_info.value)

    def test_cors_empty_rejected(self):
        """测试：空 CORS 配置被拒绝"""
        from pydantic import ValidationError
        from backend.config import Settings

        with pytest.raises(ValidationError):
            Settings(APP_ENV="development", CORS_ORIGINS="")


# ── JWT Token 过期测试 ──

class TestJWTTokenExpiry:
    """JWT Token 过期时间测试"""

    def test_jwt_token_expiry(self):
        """测试：访问令牌 30 分钟过期"""
        from datetime import timedelta

        token = create_access_token(data={"sub": "1", "role": "admin", "org_id": 1})
        payload = verify_token(token)

        assert payload is not None
        assert payload["type"] == "access"

        # 检查过期时间约为 30 分钟
        from datetime import datetime
        exp = datetime.utcfromtimestamp(payload["exp"])
        iat = datetime.utcfromtimestamp(payload["iat"])
        delta = (exp - iat).total_seconds()
        assert abs(delta - ACCESS_TOKEN_EXPIRE_MINUTES * 60) < 5  # 5 秒误差

    def test_refresh_token_expiry(self):
        """测试：刷新令牌 7 天过期"""
        token = create_refresh_token(data={"sub": "1", "role": "admin", "org_id": 1})
        payload = verify_token(token)

        assert payload is not None
        assert payload["type"] == "refresh"

        from datetime import datetime
        exp = datetime.utcfromtimestamp(payload["exp"])
        iat = datetime.utcfromtimestamp(payload["iat"])
        delta = (exp - iat).total_seconds()
        expected = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        assert abs(delta - expected) < 5

    def test_token_blacklist(self):
        """测试：Token 黑名单生效"""
        token = create_access_token(data={"sub": "123", "role": "admin", "org_id": 1})

        # 先验证正常
        assert verify_token(token) is not None

        # 加入黑名单
        blacklist_token(token)

        # 再次验证应返回 None
        assert verify_token(token) is None

    def test_invalid_token_returns_none(self):
        """测试：无效 token 返回 None"""
        assert verify_token("invalid.token.here") is None
        assert verify_token("") is None


# ── API Key 验证测试 ──

class TestApiKeyValidation:
    """API Key 验证测试"""

    def test_api_key_generation(self):
        """测试：API Key 生成格式正确"""
        key = generate_api_key()
        assert key.startswith("fai_")
        assert len(key) > 10

    def test_api_key_hash_deterministic(self):
        """测试：同一 key 的哈希一致"""
        key = "fai_test_key_123"
        h1 = hash_api_key(key)
        h2 = hash_api_key(key)
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex

    def test_api_key_hash_different(self):
        """测试：不同 key 的哈希不同"""
        h1 = hash_api_key("fai_key_1")
        h2 = hash_api_key("fai_key_2")
        assert h1 != h2

    def test_api_key_hash_not_reversible(self):
        """测试：无法从哈希反推原始 key"""
        key = "fai_original_key"
        h = hash_api_key(key)
        assert key not in h
        assert h != key
