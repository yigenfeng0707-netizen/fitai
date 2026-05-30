"""
API Key 管理模块
- API Key 生成与验证
- Key 轮换支持
- 密钥哈希存储（不存明文）
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.auth import ApiKey, User
from backend.core.security import get_password_hash, verify_password


# ── Key 生成 ──

KEY_PREFIX = "fai"  # FitAI
KEY_LENGTH = 32      # 随机部分长度


def generate_api_key() -> str:
    """生成新的 API Key（明文，仅返回一次给用户）"""
    random_part = secrets.token_hex(KEY_LENGTH)
    return f"{KEY_PREFIX}_{random_part}"


def hash_api_key(api_key: str) -> str:
    """对 API Key 进行哈希（用于存储）"""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


# ── Key 管理 ──

class ApiKeyService:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        name: str,
        organization_id: int,
        expires_in_days: int = 90,
    ) -> tuple[str, ApiKey]:
        """
        创建 API Key。
        返回 (明文key, ApiKey模型)。明文仅此一次返回。
        """
        plaintext_key = generate_api_key()
        key_hash = hash_api_key(plaintext_key)

        api_key = ApiKey(
            name=name,
            key_hash=key_hash,
            user_id=user_id,
            organization_id=organization_id,
            is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
        )
        db.add(api_key)
        await db.flush()

        return plaintext_key, api_key

    @staticmethod
    async def validate(
        db: AsyncSession,
        raw_key: str,
    ) -> Optional[ApiKey]:
        """
        验证 API Key 是否有效。
        返回 ApiKey 对象或 None。
        """
        key_hash = hash_api_key(raw_key)

        result = await db.execute(
            select(ApiKey).where(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True,  # noqa: E712
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # 检查是否过期
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None

        # 更新最后使用时间
        api_key.last_used_at = datetime.now(timezone.utc)
        await db.flush()

        return api_key

    @staticmethod
    async def rotate(
        db: AsyncSession,
        key_id: int,
        user_id: int,
        organization_id: int,
    ) -> tuple[str, ApiKey]:
        """
        轮换 API Key：禁用旧 Key，创建新 Key。
        返回 (新明文key, 新ApiKey模型)。
        """
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == user_id,
                ApiKey.organization_id == organization_id,
            )
        )
        old_key = result.scalar_one_or_none()
        if not old_key:
            raise ValueError("API Key 不存在")

        # 禁用旧 Key
        old_key.is_active = False
        old_key.revoked_at = datetime.now(timezone.utc)

        # 创建新 Key
        return await ApiKeyService.create(
            db,
            user_id=user_id,
            name=old_key.name,
            organization_id=organization_id,
            expires_in_days=90,
        )

    @staticmethod
    async def revoke(
        db: AsyncSession,
        key_id: int,
        user_id: int,
        organization_id: int,
    ) -> None:
        """撤销 API Key"""
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == user_id,
                ApiKey.organization_id == organization_id,
            )
        )
        api_key = result.scalar_one_or_none()
        if not api_key:
            raise ValueError("API Key 不存在")

        api_key.is_active = False
        api_key.revoked_at = datetime.now(timezone.utc)
        await db.flush()

    @staticmethod
    async def list_keys(
        db: AsyncSession,
        user_id: int,
        organization_id: int,
    ) -> list[ApiKey]:
        """列出用户的所有 API Key（不含哈希）"""
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.user_id == user_id,
                ApiKey.organization_id == organization_id,
            ).order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())
