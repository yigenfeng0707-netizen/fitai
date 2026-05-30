"""
数据库模型 - 门店
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin


class Store(Base, TenantMixin):
    """门店表"""
    __tablename__ = "stores"

    __table_args__ = (
        Index("ix_stores_org_code", "organization_id", "code", unique=True),
        Index("ix_stores_org_active", "organization_id", "is_active"),
        Index("ix_stores_org_city", "organization_id", "city"),
        Index("ix_stores_manager", "manager_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    address = Column(String(200), nullable=True)
    city = Column(String(50), nullable=True)
    district = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    manager_id = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True)

    business_hours = Column(JSON, nullable=True)
    facilities = Column(JSON, nullable=True)
    max_capacity = Column(Integer, default=0)
    settings = Column(JSON, nullable=True)

    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
