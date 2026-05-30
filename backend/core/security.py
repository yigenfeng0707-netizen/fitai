"""
安全工具: 密码哈希、JWT、Token 黑名单
"""
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from backend.config import settings


# ── 密码哈希 ──

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ── JWT Token ──

# Token 过期时间
ACCESS_TOKEN_EXPIRE_MINUTES = 30   # 访问令牌 30 分钟
REFRESH_TOKEN_EXPIRE_DAYS = 7      # 刷新令牌 7 天


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌（默认 30 分钟过期）"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌（7 天过期）"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证令牌（同时检查黑名单）"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None

    # 检查 token 是否在黑名单中
    jti = payload.get("jti") or payload.get("sub")
    if jti and _token_blacklist.is_blacklisted(jti, payload.get("exp")):
        return None

    return payload


# ── Token 黑名单 ──

class _TokenBlacklist:
    """
    内存 Token 黑名单（支持 TTL 自动清理）。
    生产环境建议迁移到 Redis。
    """

    def __init__(self):
        # {identifier: expiry_timestamp}
        self._blacklist: dict[str, float] = {}
        self._last_prune: float = 0.0

    def add(self, identifier: str, expiry: float) -> None:
        """将 token 加入黑名单"""
        self._blacklist[identifier] = expiry
        self._prune()

    def is_blacklisted(self, identifier: str, expiry: Optional[float] = None) -> bool:
        """检查 token 是否在黑名单中"""
        if identifier not in self._blacklist:
            return False
        # 如果 token 已自然过期，无需在黑名单中
        if expiry and expiry < time.time():
            self._blacklist.pop(identifier, None)
            return False
        return True

    def _prune(self) -> None:
        """清理已过期的黑名单记录"""
        now = time.time()
        if now - self._last_prune < 300:  # 每 5 分钟清理一次
            return
        self._last_prune = now
        expired = [k for k, v in self._blacklist.items() if v < now]
        for k in expired:
            del self._blacklist[k]

    def blacklist_token(self, token: str) -> None:
        """
        将整个 JWT token 加入黑名单。
        解析 token 获取 jti/sub 和 exp。
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError:
            return

        identifier = payload.get("jti") or payload.get("sub")
        expiry = payload.get("exp", 0)
        if identifier:
            self.add(identifier, expiry)


# 全局黑名单实例
_token_blacklist = _TokenBlacklist()


def blacklist_token(token: str) -> None:
    """将 token 加入黑名单（用于登出）"""
    _token_blacklist.blacklist_token(token)
