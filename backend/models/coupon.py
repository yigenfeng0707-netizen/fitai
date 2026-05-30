from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from backend.database_base import Base, TenantMixin


class CouponType(str, Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class Coupon(TenantMixin, Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    coupon_type = Column(String(20), nullable=False, default=CouponType.FIXED)
    value = Column(Float, nullable=False)
    min_amount = Column(Float, default=0.0)
    max_discount = Column(Float, nullable=True)

    total_count = Column(Integer, default=0)
    used_count = Column(Integer, default=0)

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class CouponUsage(TenantMixin, Base):
    __tablename__ = "coupon_usages"

    __table_args__ = (
        Index("ix_couponusage_org_coupon_created", "organization_id", "coupon_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    coupon_id = Column(Integer, nullable=False, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    order_id = Column(Integer, nullable=True)

    discount_amount = Column(Float, default=0.0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
