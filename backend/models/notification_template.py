"""
数据库模型 - 通知模板
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON

from backend.database_base import Base, TenantMixin


class NotificationTemplate(Base, TenantMixin):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    title_template = Column(String(200), nullable=False)
    content_template = Column(String(1000), nullable=False)
    channels = Column(JSON, default=["in_app"])
    notification_type = Column(String(50), default="system")
    variables = Column(JSON, default=[])  # list of variable names
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
