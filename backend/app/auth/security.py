from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.settings import settings
from app.database import SessionLocal
from app.models.user import User, LoginLog

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    """安全认证服务"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码加密"""
        return pwd_context.hash(password)
    
    @staticmethod
    def check_password_strength(password: str) -> tuple[bool, str]:
        """
        检查密码强度
        要求：至少8位，包含大小写字母和数字
        """
        if len(password) < 8:
            return False, "密码长度至少8位"
        if not any(c.isupper() for c in password):
            return False, "密码必须包含大写字母"
        if not any(c.islower() for c in password):
            return False, "密码必须包含小写字母"
        if not any(c.isdigit() for c in password):
            return False, "密码必须包含数字"
        return True, "密码强度合格"
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """解码令牌"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """验证令牌"""
        payload = AuthService.decode_token(token)
        if payload and payload.get("type") == token_type:
            return payload
        return None

class LoginSecurity:
    """登录安全服务"""
    
    MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数
    LOCKOUT_DURATION = 30   # 锁定时长（分钟）
    
    @staticmethod
    def record_login_attempt(db, username: str, ip_address: str, user_agent: str, success: bool) -> None:
        """记录登录尝试"""
        log = LoginLog(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            attempt_time=datetime.utcnow()
        )
        db.add(log)
        db.commit()
    
    @staticmethod
    def check_login_attempts(db, username: str) -> tuple[bool, int]:
        """
        检查登录尝试次数
        返回：(是否被锁定, 剩余锁定时间分钟)
        """
        lockout_start = datetime.utcnow() - timedelta(minutes=LoginSecurity.LOCKOUT_DURATION)
        
        # 查询最近LOCKOUT_DURATION分钟内的失败尝试
        failed_attempts = db.query(LoginLog).filter(
            LoginLog.username == username,
            LoginLog.success == False,
            LoginLog.attempt_time >= lockout_start
        ).count()
        
        if failed_attempts >= LoginSecurity.MAX_LOGIN_ATTEMPTS:
            # 计算剩余锁定时间
            last_attempt = db.query(LoginLog).filter(
                LoginLog.username == username,
                LoginLog.success == False
            ).order_by(LoginLog.attempt_time.desc()).first()
            
            if last_attempt:
                elapsed = datetime.utcnow() - last_attempt.attempt_time
                remaining = max(0, LoginSecurity.LOCKOUT_DURATION - int(elapsed.total_seconds() / 60))
                return True, remaining
            
        return False, 0
    
    @staticmethod
    def clear_login_attempts(db, username: str) -> None:
        """清除登录尝试记录（登录成功后）"""
        db.query(LoginLog).filter(
            LoginLog.username == username
        ).delete()
        db.commit()

class AuditLog:
    """审计日志服务"""
    
    @staticmethod
    def log_action(
        db,
        user_id: int,
        username: str,
        action: str,
        resource: str,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[str] = None
    ) -> None:
        """记录操作审计日志"""
        from app.models.user import AuditLog as AuditLogModel
        
        log = AuditLogModel(
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details,
            created_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()

class RateLimiter:
    """限流器"""
    
    _cache = {}  # 简单内存缓存，生产环境应使用Redis
    
    @classmethod
    def check_rate_limit(cls, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        检查限流
        返回：(是否允许, 剩余请求次数)
        """
        now = datetime.utcnow()
        
        if key not in cls._cache:
            cls._cache[key] = []
        
        # 清理过期记录
        cls._cache[key] = [
            t for t in cls._cache[key]
            if now - t < timedelta(seconds=window_seconds)
        ]
        
        if len(cls._cache[key]) >= max_requests:
            return False, 0
        
        cls._cache[key].append(now)
        remaining = max_requests - len(cls._cache[key])
        return True, remaining

def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_user_agent(request: Request) -> str:
    """获取User-Agent"""
    return request.headers.get("User-Agent", "unknown")
