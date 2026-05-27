from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from backend.database_base import Base


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="subscriptions")

    plan = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default=SubscriptionStatus.ACTIVE)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=False)

    amount = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    actual_amount = Column(Float, nullable=False)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    order = relationship("Order")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
