"""
数据库模型 - 会员卡交易记录
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin, StoreScopeMixin


class TransactionType(str, Enum):
    RECHARGE = "recharge"
    RENEW = "renew"
    UPGRADE = "upgrade"
    CONSUME = "consume"
    REFUND = "refund"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"


class CardTransaction(Base, TenantMixin, StoreScopeMixin):
    __tablename__ = "card_transactions"

    __table_args__ = (
        Index("ix_ctransactions_org_member_created", "organization_id", "member_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Float, default=0.0)
    count_change = Column(Integer, default=0)
    balance_before = Column(Float, default=0.0)
    balance_after = Column(Float, default=0.0)
    count_before = Column(Integer, default=0)
    count_after = Column(Integer, default=0)
    card_type_before = Column(String(20), nullable=True)
    card_type_after = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", backref="card_transactions")
    operator = relationship("User")
