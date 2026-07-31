from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.organization import Organization, PlanType
from backend.models.subscription import Subscription
from backend.schemas.common import BaseResponse, ListResponse
from backend.services.subscription import SubscriptionService, PLAN_PRICES

router = APIRouter()


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    plan: PlanType = Query(...),
    duration_months: int = Query(1, ge=1, le=12),
    amount: float = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    sub = await SubscriptionService.create(
        db, org, plan, duration_months, amount
    )
    return BaseResponse(
        message="订阅创建成功",
        data={"subscription_id": sub.id, "plan": sub.plan, "end_date": str(sub.end_date)},
    )


@router.get("/active", response_model=BaseResponse)
async def get_active_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = await SubscriptionService.get_active(db, current_user.organization_id)
    return BaseResponse(
        data={
            "has_active": sub is not None,
            "subscription": {
                "id": sub.id,
                "plan": sub.plan,
                "status": sub.status,
                "end_date": str(sub.end_date),
                "auto_renew": sub.auto_renew,
            } if sub else None,
        }
    )


@router.get("/plans", response_model=BaseResponse)
async def get_plans():
    """Return available subscription plans and prices."""
    return BaseResponse(data={
        "plans": [
            {"key": k, "name": k.capitalize(), "price": v}
            for k, v in PLAN_PRICES.items()
        ]
    })


@router.post("/{sub_id}/cancel", response_model=BaseResponse)
async def cancel_subscription(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.organization_id == current_user.organization_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    if sub.status != "active":
        raise HTTPException(status_code=400, detail="只能取消活跃订阅")
    await SubscriptionService.cancel(db, sub)
    return BaseResponse(message="订阅已取消")


@router.post("/{sub_id}/renew", response_model=BaseResponse)
async def renew_subscription(
    sub_id: int,
    duration_months: int = Query(1, ge=1, le=12),
    amount: float = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.organization_id == current_user.organization_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    sub = await SubscriptionService.renew(db, sub, duration_months, amount)
    return BaseResponse(
        message="订阅已续费",
        data={"end_date": str(sub.end_date)},
    )


@router.post("/{sub_id}/upgrade", response_model=BaseResponse)
async def upgrade_subscription(
    sub_id: int,
    new_plan: PlanType = Query(...),
    duration_months: int = Query(0, ge=0, le=12),
    amount: float = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.organization_id == current_user.organization_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    if sub.status != "active":
        raise HTTPException(status_code=400, detail="只能升级活跃订阅")
    sub = await SubscriptionService.upgrade(db, sub, new_plan, duration_months, amount)
    return BaseResponse(
        message=f"已升级到 {new_plan.value} 方案",
        data={"plan": sub.plan, "end_date": str(sub.end_date)},
    )


@router.post("/{sub_id}/toggle-renew", response_model=BaseResponse)
async def toggle_auto_renew(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == sub_id,
            Subscription.organization_id == current_user.organization_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    sub.auto_renew = not sub.auto_renew
    await db.flush()
    return BaseResponse(
        message=f"自动续费已{'开启' if sub.auto_renew else '关闭'}",
        data={"auto_renew": sub.auto_renew},
    )


@router.get("/", response_model=ListResponse)
async def get_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subs, total = await SubscriptionService.get_list(
        db, organization_id=current_user.organization_id,
        skip=skip, limit=limit,
    )
    data = []
    for s in subs:
        d = {}
        for col in s.__table__.columns:
            val = getattr(s, col.name)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            d[col.name] = val
        data.append(d)
    return ListResponse(
        data=data,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )
