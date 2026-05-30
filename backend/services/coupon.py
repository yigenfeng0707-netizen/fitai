import random
import string
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.coupon import Coupon, CouponUsage


class CouponService:
    @staticmethod
    def _generate_code(length: int = 8) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    @staticmethod
    async def create(
        db: AsyncSession,
        organization_id: int,
        name: str,
        coupon_type: str,
        value: float,
        min_amount: float = 0,
        max_discount: Optional[float] = None,
        total_count: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        code: Optional[str] = None,
    ) -> Coupon:
        coupon = Coupon(
            organization_id=organization_id,
            code=code or CouponService._generate_code(),
            name=name,
            coupon_type=coupon_type,
            value=value,
            min_amount=min_amount,
            max_discount=max_discount,
            total_count=total_count,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
        )
        db.add(coupon)
        await db.flush()
        return coupon

    @staticmethod
    async def validate(
        db: AsyncSession,
        organization_id: int,
        code: str,
        amount: float,
    ) -> Coupon:
        result = await db.execute(
            select(Coupon).where(
                Coupon.organization_id == organization_id,
                Coupon.code == code.upper(),
                Coupon.is_active == True,
            )
        )
        coupon = result.scalar_one_or_none()
        if not coupon:
            raise ValueError("优惠券不存在或已禁用")
        now = datetime.now(timezone.utc)
        if coupon.start_date and now < coupon.start_date:
            raise ValueError("优惠券尚未生效")
        if coupon.end_date and now > coupon.end_date:
            raise ValueError("优惠券已过期")
        if coupon.total_count > 0 and coupon.used_count >= coupon.total_count:
            raise ValueError("优惠券已用完")
        if amount < coupon.min_amount:
            raise ValueError(f"订单金额需满 ¥{coupon.min_amount}")
        return coupon

    @staticmethod
    def calculate_discount(coupon: Coupon, amount: float) -> float:
        if coupon.coupon_type == "percent":
            discount = amount * (coupon.value / 100)
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        else:
            discount = min(coupon.value, amount)
        return round(discount, 2)

    @staticmethod
    async def use_coupon(
        db: AsyncSession,
        coupon: Coupon,
        member_id: int,
        order_id: Optional[int] = None,
        amount: float = 0,
    ) -> CouponUsage:
        discount = CouponService.calculate_discount(coupon, amount)
        coupon.used_count += 1
        usage = CouponUsage(
            organization_id=coupon.organization_id,
            coupon_id=coupon.id,
            member_id=member_id,
            order_id=order_id,
            discount_amount=discount,
        )
        db.add(usage)
        await db.flush()
        return usage

    @staticmethod
    async def get_list(
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Coupon], int]:
        query = select(Coupon).where(Coupon.organization_id == organization_id)
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        query = query.offset(skip).limit(limit).order_by(Coupon.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all()), total or 0

    @staticmethod
    async def get_usage_list(
        db: AsyncSession,
        organization_id: int,
        coupon_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[CouponUsage], int]:
        query = select(CouponUsage).where(CouponUsage.organization_id == organization_id)
        if coupon_id:
            query = query.where(CouponUsage.coupon_id == coupon_id)
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        query = query.offset(skip).limit(limit).order_by(CouponUsage.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all()), total or 0

    @staticmethod
    async def toggle_active(db: AsyncSession, coupon: Coupon) -> Coupon:
        coupon.is_active = not coupon.is_active
        await db.flush()
        return coupon

    @staticmethod
    async def delete(db: AsyncSession, coupon: Coupon) -> None:
        await db.delete(coupon)
        await db.flush()
