from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum, Index

from backend.database_base import Base, TenantMixin, StoreScopeMixin


class LeadSource(str, Enum):
    CALL = "call"
    VISIT = "visit"
    REFERRAL = "referral"
    AD = "ad"
    SOCIAL = "social"
    OTHER = "other"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class LeadIntent(str, Enum):
    FITNESS = "fitness"
    YOGA = "yoga"
    TRAINING = "training"
    REHAB = "rehab"
    OTHER = "other"


class Lead(Base, TenantMixin, StoreScopeMixin):
    __tablename__ = "leads"

    __table_args__ = (
        Index("ix_leads_org_status_created", "organization_id", "status", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    gender = Column(String(10), nullable=True)
    age = Column(Integer, nullable=True)
    source = Column(SQLEnum(LeadSource), default=LeadSource.VISIT)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, index=True)
    intent = Column(SQLEnum(LeadIntent), nullable=True)

    expected_budget = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    follow_up_count = Column(Integer, default=0)
    last_contacted_at = Column(DateTime, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    converted_member_id = Column(Integer, ForeignKey("members.id"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
