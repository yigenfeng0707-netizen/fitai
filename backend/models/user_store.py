"""
数据库模型 - 用户门店关联
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin


class UserStore(Base, TenantMixin):
    """用户门店关联表"""
    __tablename__ = "user_stores"

    __table_args__ = (
        Index("ix_userstores_user_store", "user_id", "store_id", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    role_at_store = Column(String(50), nullable=True)
    is_primary = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    store = relationship("Store")
