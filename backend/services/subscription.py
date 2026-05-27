from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.organization import Organization, PlanType
from backend.models.subscription import Subscription, SubscriptionStatus


class SubscriptionService:
    @staticmethod
    async def create(
        db: AsyncSession,
        organization: Organization,
        plan: PlanType,
        duration_months: int = 1,
        amount: float = 0.0,
        order_id: Optional[int] = None,
    ) -> Subscription:
        now = datetime.utcnow()
        sub = Subscription(
            organization_id=organization.id,
            plan=plan.value,
            status=SubscriptionStatus.ACTIVE,
            start_date=now,
            end_date=now + timedelta(days=30 * duration_months),
            auto_renew=False,
            amount=amount,
            discount=0.0,
            actual_amount=amount,
            order_id=order_id,
        )
        db.add(sub)
        await db.flush()

        organization.plan = plan.value
        await db.flush()
        return sub

    @staticmethod
    async def get_active(db: AsyncSession, organization_id: int) -> Optional[Subscription]:
        result = await db.execute(
            select(Subscription).where(
                Subscription.organization_id == organization_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            ).order_by(Subscription.end_date.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def cancel(db: AsyncSession, subscription: Subscription) -> Subscription:
        subscription.status = SubscriptionStatus.CANCELLED
        await db.flush()
        return subscription

    @staticmethod
    async def check_expired(db: AsyncSession) -> list[Subscription]:
        now = datetime.utcnow()
        result = await db.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date < now,
            )
        )
        expired = list(result.scalars().all())
        for sub in expired:
            sub.status = SubscriptionStatus.EXPIRED
            if not sub.auto_renew:
                sub.status = SubscriptionStatus.EXPIRED
        await db.flush()
        return expired

    @staticmethod
    async def get_list(
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Subscription], int]:
        from sqlalchemy import func

        query = select(Subscription).where(
            Subscription.organization_id == organization_id
        )
        total_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar()

        query = query.offset(skip).limit(limit).order_by(Subscription.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all()), total or 0
