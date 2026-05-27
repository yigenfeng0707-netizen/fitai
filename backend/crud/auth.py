"""
CRUD - 认证
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.auth import User
from backend.core.security import get_password_hash, verify_password


class UserCRUD:
    """用户 CRUD"""
    
    @staticmethod
    async def get(db: AsyncSession, user_id: int) -> Optional[User]:
        """获取用户"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, username: str, password: str, role: str = "receptionist", organization_id: int = 1) -> User:
        """创建用户"""
        hashed_password = get_password_hash(password)

        user = User(
            username=username,
            password_hash=hashed_password,
            role=role,
            organization_id=organization_id,
        )
        
        db.add(user)
        await db.flush()
        return user
    
    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """认证用户"""
        user = await UserCRUD.get_by_username(db, username)
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    async def update_last_login(db: AsyncSession, user: User) -> User:
        """更新最后登录时间"""
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        await db.flush()
        return user