from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, JSON, Enum as SQLEnum,
)

from backend.database_base import Base, TenantMixin


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignChannel(str, Enum):
    SMS = "sms"
    WECHAT = "wechat"
    CALL = "call"
    SOCIAL = "social"
    EMAIL = "email"
    OFFLINE = "offline"


class Campaign(Base, TenantMixin):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(String(50), nullable=False, default="promotion")
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT, index=True)
    channels = Column(JSON, nullable=True)

    target_audience = Column(JSON, nullable=True)
    target_count = Column(Integer, default=0)
    budget = Column(Float, default=0)
    actual_cost = Column(Float, default=0)

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    sent_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    converted_count = Column(Integer, default=0)
    converted_revenue = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
