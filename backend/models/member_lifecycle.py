"""
数据库模型 - 会员生命周期事件
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, JSON, Index
from backend.database_base import Base, TenantMixin


class MemberLifecycleEvent(Base, TenantMixin):
    """会员生命周期事件表"""
    __tablename__ = "member_lifecycle_events"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # register, first_visit, card_purchase, card_renew, card_expire, freeze, unfreeze, churn, reactivate
    event_date = Column(Date, nullable=False, index=True)
    event_data = Column(JSON)  # additional data about the event
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_lifecycle_org_member_date', 'organization_id', 'member_id', 'event_date'),
    )
