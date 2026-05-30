"""
数据库模型 - 消息通知
"""
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean, JSON, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin


class NotificationType(str, Enum):
    SYSTEM = "system"
    CLASS_REMINDER = "class_reminder"
    CARD_EXPIRING = "card_expiring"
    CARD_EXPIRED = "card_expired"
    BOOKING_CONFIRM = "booking_confirm"
    BOOKING_CANCEL = "booking_cancel"
    PAYMENT_SUCCESS = "payment_success"
    MARKETING = "marketing"


class Notification(Base, TenantMixin):
    __tablename__ = "notifications"

    __table_args__ = (
        Index("ix_notifications_org_user_read_created", "organization_id", "user_id", "is_read", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    notification_type = Column(SQLEnum(NotificationType), nullable=False, default=NotificationType.SYSTEM)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    link = Column(String(500), nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="notifications")
