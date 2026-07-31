"""
数据库模型 - 订单
"""
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin, StoreScopeMixin


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"         # 待支付
    PAID = "paid"               # 已支付
    REFUNDED = "refunded"       # 已退款
    CANCELLED = "cancelled"     # 已取消


class PaymentMethod(str, Enum):
    """支付方式"""
    WECHAT = "wechat"
    ALIPAY = "alipay"
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"


class ProductType(str, Enum):
    """商品类型"""
    CARD = "card"               # 会员卡
    COURSE = "course"           # 课程
    SERVICE = "service"         # 服务
    SUBSCRIPTION = "subscription"  # SaaS订阅


class Order(Base, TenantMixin, StoreScopeMixin):
    """订单表"""
    __tablename__ = "orders"

    __table_args__ = (
        Index("ix_orders_org_paystatus_paidat", "organization_id", "payment_status", "paid_at"),
        Index("ix_orders_org_member_created", "organization_id", "member_id", "created_at"),
        Index("ix_orders_org_created", "organization_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    order_no = Column(String(30), unique=True, nullable=False, index=True)

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    member = relationship("Member", back_populates="orders")

    # 金额
    amount = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    actual_amount = Column(Float, nullable=False)

    # 支付
    payment_method = Column(String(20), nullable=True)
    payment_status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, index=True)
    transaction_id = Column(String(100), nullable=True)

    # 商品
    product_type = Column(String(20), nullable=True)
    product_id = Column(Integer, nullable=True)
    subject = Column(String(200), nullable=True)

    # 操作人
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    operator = relationship("User", back_populates="orders")

    # 备注
    notes = Column(String(200), nullable=True)
    cancel_reason = Column(String(200), nullable=True)

    # 退款
    refund_amount = Column(Float, default=0.0)
    refunded_at = Column(DateTime, nullable=True)

    # 时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True, index=True)
