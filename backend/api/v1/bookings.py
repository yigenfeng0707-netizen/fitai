"""
API - 预约
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.booking import Booking, BookingStatus
from backend.schemas.booking import BookingCreate, BookingUpdate, BookingResponse, BookingCheckIn
from backend.models.auth import User
from backend.schemas.common import BaseResponse, ListResponse

router = APIRouter()


@router.post("/", response_model=BookingResponse)
async def create_booking(
    obj_in: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建预约"""
    from backend.crud.booking import BookingCRUD
    try:
        booking = await BookingCRUD.create(db, obj_in, organization_id=current_user.organization_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return booking


@router.get("/today", response_model=ListResponse[BookingResponse])
async def get_today_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取今日预约"""
    from backend.crud.booking import BookingCRUD
    from datetime import datetime
    bookings = await BookingCRUD.get_today_bookings(db, datetime.utcnow())
    
    return ListResponse(
        data=bookings,
        total=len(bookings),
        page=1,
        page_size=len(bookings),
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取预约详情"""
    from backend.crud.booking import BookingCRUD
    booking = await BookingCRUD.get(db, booking_id)
    if not booking or booking.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在",
        )
    return booking


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    obj_in: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新预约"""
    from backend.crud.booking import BookingCRUD
    booking = await BookingCRUD.get(db, booking_id)
    if not booking or booking.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在",
        )
    
    booking = await BookingCRUD.update(db, booking, obj_in)
    return booking


@router.post("/{booking_id}/cancel", response_model=BaseResponse)
async def cancel_booking(
    booking_id: int,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消预约"""
    from backend.crud.booking import BookingCRUD
    booking = await BookingCRUD.get(db, booking_id)
    if not booking or booking.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在",
        )
    
    if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"预约状态不允许取消: {booking.status.value}",
        )
    
    booking = await BookingCRUD.cancel(db, booking, current_user.id, reason)
    return BaseResponse(message="取消成功")


@router.post("/{booking_id}/checkin", response_model=BookingResponse)
async def checkin_booking(
    booking_id: int,
    obj_in: BookingCheckIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """签到"""
    from backend.crud.booking import BookingCRUD
    booking = await BookingCRUD.get(db, booking_id)
    if not booking or booking.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在",
        )
    
    if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"预约状态不允许签到: {booking.status.value}",
        )
    
    booking = await BookingCRUD.check_in(db, booking, obj_in.check_in_method)
    return booking


@router.get("/checkin/today")
async def get_checkin_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取今日签到数据（含会员名、课程名，按排期分组）"""
    from backend.crud.booking import BookingCRUD
    from datetime import datetime
    stats = await BookingCRUD.get_today_stats(db, datetime.utcnow(), organization_id=current_user.organization_id)
    return stats


@router.get("/", response_model=ListResponse[BookingResponse])
async def get_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    member_id: Optional[int] = None,
    schedule_id: Optional[int] = None,
    status: Optional[BookingStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取预约列表"""
    from backend.crud.booking import BookingCRUD
    bookings, total = await BookingCRUD.get_list(
        db, skip=skip, limit=limit,
        member_id=member_id, schedule_id=schedule_id, status=status,
        organization_id=current_user.organization_id,
    )
    
    return ListResponse(
        data=bookings,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )