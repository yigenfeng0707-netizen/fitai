from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.orm import relationship
import enum

from backend.database_base import Base, TenantMixin


class AutomationTriggerType(str, enum.Enum):
    MEMBER_CREATED = "member_created"
    CARD_EXPIRING = "card_expiring"
    BOOKING_CANCELLED = "booking_cancelled"
    LEAD_CREATED = "lead_created"
    LEAD_STATUS_CHANGED = "lead_status_changed"
    MEMBER_INACTIVE = "member_inactive"
    BIRTHDAY = "birthday"


class AutomationActionType(str, enum.Enum):
    SEND_NOTIFICATION = "send_notification"


class AutomationRule(TenantMixin, Base):
    __tablename__ = "automation_rules"

    __table_args__ = (
        Index("ix_arules_org_trigger_active", "organization_id", "trigger_type", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(SAEnum(AutomationTriggerType), nullable=False, index=True)
    trigger_config = Column(JSON, nullable=True)
    action_type = Column(SAEnum(AutomationActionType), nullable=False)
    action_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    logs = relationship("AutomationLog", back_populates="rule")


class AutomationLog(TenantMixin, Base):
    __tablename__ = "automation_logs"

    __table_args__ = (
        Index("ix_alogs_org_rule_created", "organization_id", "rule_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("automation_rules.id"), nullable=False, index=True)
    trigger_entity_type = Column(String(50), nullable=False)
    trigger_entity_id = Column(Integer, nullable=True)
    action_result = Column(JSON, nullable=True)
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    rule = relationship("AutomationRule", back_populates="logs")
