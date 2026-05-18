"""
FitAI - 安全功能测试脚本
Phase 1: JWT认证与登录安全测试
"""
import pytest
import time
from datetime import datetime, timedelta
from app.auth.security import AuthService, LoginSecurity, RateLimiter, get_client_ip
from app.database import SessionLocal
from app.models.user import User, LoginLog

class TestJWTAuthentication:
    """JWT认证测试"""
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": "123", "username": "test"}
        token = AuthService.create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        print("✅ 创建访问令牌成功")
    
    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        data = {"sub": "123"}
        token = AuthService.create_refresh_token(data)
        assert token is not None
        assert isinstance(token, str)
        print("✅ 创建刷新令牌成功")
    
    def test_decode_token(self):
        """测试解码令牌"""
        data = {"sub": "123", "username": "test"}
        token = AuthService.create_access_token(data)
        payload = AuthService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["username"] == "test"
        print("✅ 解码令牌成功")
    
    def test_verify_token_with_type(self):
        """测试令牌类型验证"""
        access_data = {"sub": "123"}
        access_token = AuthService.create_access_token(access_data)
        refresh_token = AuthService.create_refresh_token(access_data)
        
        # 验证access_token
        payload = AuthService.verify_token(access_token, token_type="access")
        assert payload is not None
        print("✅ Access Token类型验证成功")
        
        # 验证refresh_token
        payload = AuthService.verify_token(refresh_token, token_type="refresh")
        assert payload is not None
        print("✅ Refresh Token类型验证成功")
    
    def test_expired_token_rejected(self):
        """测试过期令牌被拒绝"""
        data = {"sub": "123"}
        # 创建1秒过期的令牌
        token = AuthService.create_access_token(data, expires_delta=timedelta(seconds=1))
        time.sleep(2)
        payload = AuthService.verify_token(token, token_type="access")
        assert payload is None
        print("✅ 过期令牌被正确拒绝")

class TestPasswordSecurity:
    """密码安全测试"""
    
    def test_password_hashing(self):
        """测试密码哈希"""
        password = "Test@123"
        hashed = AuthService.hash_password(password)
        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        print("✅ 密码哈希成功")
    
    def test_password_verification(self):
        """测试密码验证"""
        password = "Test@123"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("WrongPassword", hashed)
        print("✅ 密码验证成功")
    
    def test_password_strength_check(self):
        """测试密码强度检查"""
        # 弱密码测试
        weak_passwords = [
            "12345678",      # 无大写
            "ABCDEFGH",      # 无小写
            "AbCdEfGh",      # 无数字
            "password",      # 太简单
        ]
        for pwd in weak_passwords:
            is_strong, msg = AuthService.check_password_strength(pwd)
            assert not is_strong
        print("✅ 弱密码被正确拒绝")
        
        # 强密码测试
        strong_password = "Test@1234"
        is_strong, msg = AuthService.check_password_strength(strong_password)
        assert is_strong
        print("✅ 强密码通过检查")

class TestLoginSecurity:
    """登录安全测试"""
    
    def test_record_login_attempt(self):
        """测试记录登录尝试"""
        db = SessionLocal()
        try:
            LoginSecurity.record_login_attempt(
                db=db,
                username="test_user",
                ip_address="127.0.0.1",
                user_agent="Test Browser",
                success=True
            )
            
            # 查询记录
            log = db.query(LoginLog).filter(
                LoginLog.username == "test_user"
            ).first()
            assert log is not None
            assert log.success == True
            print("✅ 登录尝试记录成功")
        finally:
            db.close()
    
    def test_brute_force_protection(self):
        """测试暴力破解防护"""
        db = SessionLocal()
        try:
            # 清除之前的测试记录
            db.query(LoginLog).filter(
                LoginLog.username == "bruteforce_test"
            ).delete()
            db.commit()
            
            # 模拟5次失败登录
            for i in range(5):
                LoginSecurity.record_login_attempt(
                    db=db,
                    username="bruteforce_test",
                    ip_address="127.0.0.1",
                    user_agent="Test",
                    success=False
                )
            
            # 第6次应该被锁定
            is_locked, remaining = LoginSecurity.check_login_attempts(db, "bruteforce_test")
            assert is_locked
            print(f"✅ 暴力破解防护生效，剩余锁定时间: {remaining}分钟")
            
            # 清理
            db.query(LoginLog).filter(
                LoginLog.username == "bruteforce_test"
            ).delete()
            db.commit()
        finally:
            db.close()
    
    def test_login_attempts_cleared_after_success(self):
        """测试登录成功后清除失败记录"""
        db = SessionLocal()
        try:
            # 记录失败尝试
            LoginSecurity.record_login_attempt(
                db=db,
                username="success_test",
                ip_address="127.0.0.1",
                user_agent="Test",
                success=False
            )
            
            # 登录成功，清除记录
            LoginSecurity.clear_login_attempts(db, "success_test")
            
            # 验证记录已清除
            is_locked, _ = LoginSecurity.check_login_attempts(db, "success_test")
            assert not is_locked
            print("✅ 登录成功后失败记录被清除")
            
            # 清理
            db.query(LoginLog).filter(
                LoginLog.username == "success_test"
            ).delete()
            db.commit()
        finally:
            db.close()

class TestRateLimiter:
    """限流测试"""
    
    def test_rate_limiting(self):
        """测试限流"""
        # 重置限流器
        RateLimiter._cache = {}
        
        key = "test_rate_limit"
        max_requests = 5
        
        # 前5次应该通过
        for i in range(5):
            allowed, remaining = RateLimiter.check_rate_limit(key, max_requests, 60)
            assert allowed
            assert remaining == max_requests - i - 1
        
        # 第6次应该被限制
        allowed, remaining = RateLimiter.check_rate_limit(key, max_requests, 60)
        assert not allowed
        print("✅ 限流功能生效")
    
    def test_rate_limit_window_expiry(self):
        """测试限流窗口过期"""
        # 重置限流器
        RateLimiter._cache = {}
        
        key = "test_window"
        # 使用1秒的窗口
        allowed, _ = RateLimiter.check_rate_limit(key, 1, 1)
        assert allowed
        
        # 等待窗口过期
        time.sleep(2)
        
        # 应该重新允许
        allowed, remaining = RateLimiter.check_rate_limit(key, 1, 1)
        assert allowed
        print("✅ 限流窗口过期后重新允许请求")

class TestSecurityIntegration:
    """安全集成测试"""
    
    def test_complete_login_flow(self):
        """测试完整登录流程"""
        db = SessionLocal()
        try:
            # 1. 清理测试数据
            db.query(LoginLog).filter(
                LoginLog.username == "integration_test"
            ).delete()
            db.query(User).filter(
                User.username == "integration_test"
            ).delete()
            db.commit()
            
            # 2. 注册用户（检查密码强度）
            password = "Test@1234"
            is_strong, msg = AuthService.check_password_strength(password)
            assert is_strong, f"密码强度不足: {msg}"
            
            hashed = AuthService.hash_password(password)
            user = User(
                username="integration_test",
                hashed_password=hashed,
                role_id=3,
                role_name="前台"
            )
            db.add(user)
            db.commit()
            
            # 3. 验证登录
            assert AuthService.verify_password(password, hashed)
            print("✅ 完整登录流程测试通过")
            
            # 4. 清理
            db.query(User).filter(
                User.username == "integration_test"
            ).delete()
            db.commit()
        finally:
            db.close()
    
    def test_security_headers_format(self):
        """测试安全响应头格式（验证get_client_ip）"""
        class MockRequest:
            def __init__(self):
                self.client = type('obj', (object,), {'host': '127.0.0.1'})()
                self.headers = {'User-Agent': 'Test'}
        
        request = MockRequest()
        ip = get_client_ip(request)
        assert ip == "127.0.0.1"
        print("✅ 客户端IP获取正确")

def run_all_tests():
    """运行所有安全测试"""
    print("\n" + "="*60)
    print("FitAI 安全功能测试")
    print("Phase 1: JWT认证与登录安全")
    print("="*60 + "\n")
    
    test_classes = [
        TestJWTAuthentication,
        TestPasswordSecurity,
        TestLoginSecurity,
        TestRateLimiter,
        TestSecurityIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📂 {test_class.__name__}")
        print("-" * 40)
        
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith('test_')]
        
        for method_name in methods:
            try:
                method = getattr(instance, method_name)
                method()
                total_tests += 1
                passed_tests += 1
            except Exception as e:
                total_tests += 1
                print(f"❌ {method_name}: {str(e)}")
    
    print("\n" + "="*60)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")
    print("="*60 + "\n")
    
    if passed_tests == total_tests:
        print("🎉 所有安全测试通过！Phase 1 完成。")
    else:
        print(f"⚠️  有 {total_tests - passed_tests} 项测试失败，需要修复。")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
