from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.schemas.common import BaseResponse, ListResponse
from backend.services.coupon import CouponService

router = APIRouter()


class CouponCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    coupon_type: str = Field(..., pattern="^(percent|fixed)$")
    value: float = Field(..., gt=0)
    min_amount: float = Field(default=0, ge=0)
    max_discount: Optional[float] = None
    total_count: int = Field(default=100, ge=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    code: Optional[str] = None


class CouponValidateRequest(BaseModel):
    code: str
    amount: float


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    obj_in: CouponCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start = datetime.fromisoformat(obj_in.start_date) if obj_in.start_date else None
    end = datetime.fromisoformat(obj_in.end_date) if obj_in.end_date else None
    try:
        coupon = await CouponService.create(
            db, current_user.organization_id,
            name=obj_in.name, coupon_type=obj_in.coupon_type,
            value=obj_in.value, min_amount=obj_in.min_amount,
            max_discount=obj_in.max_discount, total_count=obj_in.total_count,
            start_date=start, end_date=end, code=obj_in.code,
        )
        return BaseResponse(message="优惠券创建成功", data={"id": coupon.id, "code": coupon.code})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ListResponse)
async def get_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    coupons, total = await CouponService.get_list(db, current_user.organization_id, skip, limit)
    data = []
    for c in coupons:
        d = {}
        for col in c.__table__.columns:
            val = getattr(c, col.name)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            d[col.name] = val
        data.append(d)
    return ListResponse(data=data, total=total, page=skip // limit + 1 if skip else 1, page_size=limit)


@router.post("/validate", response_model=BaseResponse)
async def validate_coupon(
    obj_in: CouponValidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        coupon = await CouponService.validate(db, current_user.organization_id, obj_in.code, obj_in.amount)
        discount = CouponService.calculate_discount(coupon, obj_in.amount)
        return BaseResponse(data={
            "coupon_id": coupon.id, "code": coupon.code, "name": coupon.name,
            "discount": discount, "final_amount": round(obj_in.amount - discount, 2),
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{coupon_id}/toggle", response_model=BaseResponse)
async def toggle_coupon(
    coupon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    from backend.models.coupon import Coupon
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id, Coupon.organization_id == current_user.organization_id))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    await CouponService.toggle_active(db, coupon)
    return BaseResponse(message=f"优惠券已{'启用' if coupon.is_active else '禁用'}")


@router.delete("/{coupon_id}", response_model=BaseResponse)
async def delete_coupon(
    coupon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    from backend.models.coupon import Coupon
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id, Coupon.organization_id == current_user.organization_id))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    await CouponService.delete(db, coupon)
    return BaseResponse(message="优惠券已删除")


@router.get("/{coupon_id}/usages", response_model=ListResponse)
async def get_coupon_usages(
    coupon_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usages, total = await CouponService.get_usage_list(db, current_user.organization_id, coupon_id, skip, limit)
    data = []
    for u in usages:
        d = {}
        for col in u.__table__.columns:
            val = getattr(u, col.name)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            d[col.name] = val
        data.append(d)
    return ListResponse(data=data, total=total, page=skip // limit + 1 if skip else 1, page_size=limit)
