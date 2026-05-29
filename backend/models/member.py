"""
数据库模型 - 会员
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin, StoreScopeMixin


class CardType(str, Enum):
    """卡种类型"""
    SINGLE = "single"           # 次卡
    MONTHLY = "monthly"         # 月卡
    QUARTERLY = "quarterly"     # 季卡
    YEARLY = "yearly"           # 年卡
    STORED = "stored"           # 储值卡


class MemberStatus(str, Enum):
    """会员状态"""
    ACTIVE = "active"           # 正常
    FROZEN = "frozen"           # 冻结
    SUSPENDED = "suspended"     # 休学
    CANCELLED = "cancelled"     # 注销


class Member(Base, TenantMixin, StoreScopeMixin):
    """会员表"""
    __tablename__ = "members"

    __table_args__ = (
        Index("ix_members_org_status", "organization_id", "status"),
        Index("ix_members_org_created", "organization_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)
    gender = Column(String(10), nullable=True)
    birthday = Column(DateTime, nullable=True)

    # 卡信息
    card_type = Column(SQLEnum(CardType), nullable=True)
    card_start_date = Column(DateTime, nullable=True)
    card_end_date = Column(DateTime, nullable=True)
    card_remaining_count = Column(Integer, default=0)  # 次卡剩余次数
    card_balance = Column(Float, default=0.0)  # 储值卡余额

    # 等级
    level = Column(Integer, default=1)  # 1-5 级
    total_consumption = Column(Float, default=0.0)  # 累计消费

    # 状态
    status = Column(SQLEnum(MemberStatus), default=MemberStatus.ACTIVE)

    # 档案
    body_test_data = Column(JSON, nullable=True)  # 体测数据
    tags = Column(JSON, nullable=True)  # 标签
    notes = Column(Text, nullable=True)  # 备注

    # 关联
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=True, index=True)
    coach = relationship("Coach", back_populates="members")

    body_test_records = relationship("BodyTestRecord", back_populates="member", order_by="BodyTestRecord.created_at.desc()")
    bookings = relationship("Booking", back_populates="member")
    orders = relationship("Order", back_populates="member")

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
