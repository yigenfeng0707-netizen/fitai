from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.organization import Organization, PlanType
from backend.models.subscription import Subscription, SubscriptionStatus


PLAN_PRICES = {
    "trial": 0,
    "basic": 99,
    "professional": 299,
    "enterprise": 899,
}


class SubscriptionService:
    @staticmethod
    async def create(
        db: AsyncSession,
        organization: Organization,
        plan: PlanType,
        duration_months: int = 1,
        amount: float = 0.0,
        order_id: Optional[int] = None,
        auto_renew: bool = False,
    ) -> Subscription:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sub = Subscription(
            organization_id=organization.id,
            plan=plan.value,
            status=SubscriptionStatus.ACTIVE,
            start_date=now,
            end_date=now + timedelta(days=30 * duration_months),
            auto_renew=auto_renew,
            amount=amount or PLAN_PRICES.get(plan.value, 0),
            discount=0.0,
            actual_amount=amount or PLAN_PRICES.get(plan.value, 0),
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
    async def renew(
        db: AsyncSession,
        subscription: Subscription,
        duration_months: int = 1,
        amount: float = 0.0,
        order_id: Optional[int] = None,
    ) -> Subscription:
        """Extend an existing subscription."""
        base = subscription.end_date if subscription.end_date and subscription.end_date > datetime.now(timezone.utc).replace(tzinfo=None) else datetime.now(timezone.utc).replace(tzinfo=None)
        subscription.end_date = base + timedelta(days=30 * duration_months)
        subscription.amount = amount or PLAN_PRICES.get(subscription.plan, 0)
        subscription.actual_amount = amount or PLAN_PRICES.get(subscription.plan, 0)
        subscription.order_id = order_id
        if subscription.status != SubscriptionStatus.ACTIVE:
            subscription.status = SubscriptionStatus.ACTIVE
        await db.flush()
        return subscription

    @staticmethod
    async def upgrade(
        db: AsyncSession,
        subscription: Subscription,
        new_plan: PlanType,
        duration_months: int = 0,
        amount: float = 0.0,
        order_id: Optional[int] = None,
    ) -> Subscription:
        """Upgrade (or downgrade) subscription plan. If duration_months=0, keep remaining days."""
        old_plan_price = PLAN_PRICES.get(subscription.plan, 0)
        new_plan_price = amount or PLAN_PRICES.get(new_plan.value, 0)

        subscription.plan = new_plan.value
        subscription.amount = new_plan_price
        subscription.actual_amount = new_plan_price
        subscription.order_id = order_id

        if duration_months > 0:
            base = subscription.end_date if subscription.end_date and subscription.end_date > datetime.now(timezone.utc).replace(tzinfo=None) else datetime.now(timezone.utc).replace(tzinfo=None)
            subscription.end_date = base + timedelta(days=30 * duration_months)

        if subscription.status != SubscriptionStatus.ACTIVE:
            subscription.status = SubscriptionStatus.ACTIVE

        await db.flush()

        org_result = await db.execute(
            select(Organization).where(Organization.id == subscription.organization_id)
        )
        org = org_result.scalar_one_or_none()
        if org:
            org.plan = new_plan.value
            await db.flush()

        return subscription

    @staticmethod
    async def check_expired(db: AsyncSession) -> list[Subscription]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        result = await db.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date < now,
            )
        )
        expired = list(result.scalars().all())
        for sub in expired:
            if sub.auto_renew:
                sub.end_date = sub.end_date + timedelta(days=30)
            else:
                sub.status = SubscriptionStatus.EXPIRED
        if expired:
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
