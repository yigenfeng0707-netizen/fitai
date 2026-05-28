from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.organization import Organization, PlanType
from backend.schemas.common import BaseResponse, ListResponse
from backend.services.subscription import SubscriptionService

router = APIRouter()


class SubscriptionResponse(BaseResponse):
    id: int
    organization_id: int
    plan: str
    status: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    auto_renew: bool = False
    amount: float = 0.0
    actual_amount: float = 0.0
    order_id: Optional[int] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


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
    from sqlalchemy import inspect
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
