from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.order import Order, OrderStatus
from backend.schemas.order import OrderCreate
from backend.services.payment import payment_service


class OrderService:
    @staticmethod
    def _generate_order_no() -> str:
        now = datetime.utcnow()
        return f"ORD{now.strftime('%Y%m%d%H%M%S%f')[:20]}"

    @staticmethod
    async def create(
        db: AsyncSession,
        obj_in: OrderCreate,
        organization_id: int = 1,
        operator_id: Optional[int] = None,
    ) -> Order:
        order = Order(
            order_no=OrderService._generate_order_no(),
            member_id=obj_in.member_id,
            organization_id=organization_id,
            amount=obj_in.amount,
            discount=obj_in.discount,
            actual_amount=obj_in.actual_amount,
            product_type=obj_in.product_type,
            product_id=obj_in.product_id,
            subject=obj_in.subject,
            operator_id=operator_id,
            notes=obj_in.notes,
            payment_status=OrderStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db.add(order)
        await db.flush()
        return order

    @staticmethod
    async def get(db: AsyncSession, order_id: int) -> Optional[Order]:
        result = await db.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_no(db: AsyncSession, order_no: str) -> Optional[Order]:
        result = await db.execute(select(Order).where(Order.order_no == order_no))
        return result.scalar_one_or_none()

    @staticmethod
    async def pay(
        db: AsyncSession,
        order: Order,
        payment_method: str,
        transaction_id: str,
    ) -> Order:
        order.payment_method = payment_method
        order.transaction_id = transaction_id
        order.payment_status = OrderStatus.PAID
        order.paid_at = datetime.utcnow()
        await db.flush()
        return order

    @staticmethod
    async def cancel(
        db: AsyncSession,
        order: Order,
        reason: Optional[str] = None,
    ) -> Order:
        order.payment_status = OrderStatus.CANCELLED
        order.cancel_reason = reason
        await db.flush()
        return order

    @staticmethod
    async def refund(
        db: AsyncSession,
        order: Order,
        amount: float,
        reason: Optional[str] = None,
    ) -> Order:
        if order.payment_method and order.payment_method in ("wechat", "alipay"):
            gateway = payment_service.get_gateway(order.payment_method)
            result = await gateway.refund(order.order_no, amount, reason)
            if not result.success:
                return order
        order.refund_amount = amount
        order.refunded_at = datetime.utcnow()
        order.cancel_reason = reason
        if amount >= order.actual_amount:
            order.payment_status = OrderStatus.REFUNDED
        await db.flush()
        return order

    @staticmethod
    async def get_list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        member_id: Optional[int] = None,
        payment_status: Optional[OrderStatus] = None,
        organization_id: int = 1,
    ) -> tuple[list[Order], int]:
        from sqlalchemy import func

        query = select(Order).where(Order.organization_id == organization_id)

        if member_id:
            query = query.where(Order.member_id == member_id)
        if payment_status:
            query = query.where(Order.payment_status == payment_status)

        total_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar()

        query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all()), total or 0

    @staticmethod
    async def expire_pending_orders(db: AsyncSession) -> list[Order]:
        """Cancel orders past their expiration time."""
        now = datetime.utcnow()
        result = await db.execute(
            select(Order).where(
                Order.payment_status == OrderStatus.PENDING,
                Order.expires_at.isnot(None),
                Order.expires_at < now,
            )
        )
        expired = list(result.scalars().all())
        for order in expired:
            order.payment_status = OrderStatus.CANCELLED
            order.cancel_reason = "订单已过期"
        if expired:
            await db.flush()
        return expired
