"""
API - 小程序会员
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.member import Member
from backend.models.booking import Booking, BookingStatus
from backend.models.order import Order
from backend.models.notification import Notification
from backend.schemas.member import MemberUpdate
from backend.schemas.mini import (
    MiniMemberProfile,
    MiniMemberCard,
    MiniBookingItem,
    MiniNotificationItem,
)
from backend.schemas.common import BaseResponse, ListResponse

router = APIRouter(prefix="/mini", tags=["小程序-会员"])


def _get_member_from_user(user: User) -> int:
    """从用户获取关联的会员ID"""
    if not user.member_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="当前用户未关联会员信息",
        )
    return user.member_id


@router.get("/member/profile", response_model=MiniMemberProfile)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的会员资料"""
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)
    result = await db.execute(
        select(Member).where(Member.id == member_id)
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会员信息不存在",
        )

    # 获取门店名称
    store_name = None
    if member.store_id:
        from backend.models.store import Store
        store_result = await db.execute(
            select(Store.name).where(Store.id == member.store_id)
        )
        store_name = store_result.scalar_one_or_none()

    return MiniMemberProfile(
        id=member.id,
        name=member.name,
        phone=member.phone,
        gender=member.gender,
        birthday=member.birthday.date() if member.birthday else None,
        card_type=member.card_type.value if member.card_type else None,
        card_end_date=member.card_end_date.date() if member.card_end_date else None,
        card_remaining_count=member.card_remaining_count,
        card_balance=member.card_balance,
        level=f"Lv.{member.level}" if member.level else None,
        status=member.status.value if member.status else "unknown",
        store_name=store_name,
    )


@router.put("/member/profile", response_model=MiniMemberProfile)
async def update_my_profile(
    obj_in: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新我的资料"""
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)
    result = await db.execute(
        select(Member).where(Member.id == member_id)
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会员信息不存在",
        )

    update_data = obj_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(member, key, value)

    await db.flush()

    # 获取门店名称
    store_name = None
    if member.store_id:
        from backend.models.store import Store
        store_result = await db.execute(
            select(Store.name).where(Store.id == member.store_id)
        )
        store_name = store_result.scalar_one_or_none()

    return MiniMemberProfile(
        id=member.id,
        name=member.name,
        phone=member.phone,
        gender=member.gender,
        birthday=member.birthday.date() if member.birthday else None,
        card_type=member.card_type.value if member.card_type else None,
        card_end_date=member.card_end_date.date() if member.card_end_date else None,
        card_remaining_count=member.card_remaining_count,
        card_balance=member.card_balance,
        level=f"Lv.{member.level}" if member.level else None,
        status=member.status.value if member.status else "unknown",
        store_name=store_name,
    )


@router.get("/member/card", response_model=MiniMemberCard)
async def get_my_card(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的会员卡信息（余额、次数、有效期）"""
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)
    result = await db.execute(
        select(Member).where(Member.id == member_id)
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会员信息不存在",
        )

    return MiniMemberCard(
        id=member.id,
        card_type=member.card_type.value if member.card_type else None,
        card_start_date=member.card_start_date,
        card_end_date=member.card_end_date,
        card_remaining_count=member.card_remaining_count,
        card_balance=member.card_balance,
        level=member.level,
        status=member.status.value if member.status else "unknown",
    )


@router.get("/member/body-tests")
async def get_body_test_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取体测记录"""
    from sqlalchemy import select, func
    from backend.models.member import BodyTestRecord

    member_id = _get_member_from_user(current_user)

    query = select(BodyTestRecord).where(BodyTestRecord.member_id == member_id)
    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(BodyTestRecord.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    records = list(result.scalars().all())

    return ListResponse(
        data=records,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.get("/member/bookings", response_model=ListResponse[MiniBookingItem])
async def get_my_bookings(
    status_filter: Optional[BookingStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的预约记录"""
    from sqlalchemy import select, func
    from backend.models.course import CourseSchedule, Course

    member_id = _get_member_from_user(current_user)

    query = (
        select(Booking)
        .where(Booking.member_id == member_id)
    )
    if status_filter:
        query = query.where(Booking.status == status_filter)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    bookings = list(result.scalars().all())

    # 组装返回数据
    data = []
    for booking in bookings:
        # 获取排课和课程信息
        schedule_result = await db.execute(
            select(CourseSchedule).where(CourseSchedule.id == booking.schedule_id)
        )
        schedule = schedule_result.scalar_one_or_none()

        course_name = ""
        coach_name = None
        start_time = None
        end_time = None

        if schedule:
            start_time = schedule.start_time
            end_time = schedule.end_time
            course_result = await db.execute(
                select(Course).where(Course.id == schedule.course_id)
            )
            course = course_result.scalar_one_or_none()
            if course:
                course_name = course.name
                if course.coach_id:
                    from backend.models.coach import Coach
                    coach_result = await db.execute(
                        select(Coach.name).where(Coach.id == course.coach_id)
                    )
                    coach_name = coach_result.scalar_one_or_none()

        can_cancel = booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]
        can_checkin = booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]

        data.append(MiniBookingItem(
            id=booking.id,
            schedule_id=booking.schedule_id,
            course_name=course_name,
            coach_name=coach_name,
            start_time=start_time or datetime.now(timezone.utc),
            end_time=end_time or datetime.now(timezone.utc),
            status=booking.status.value,
            check_in_time=booking.check_in_time,
            can_cancel=can_cancel,
            can_checkin=can_checkin,
        ))

    return ListResponse(
        data=data,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.get("/member/orders")
async def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的订单记录"""
    from sqlalchemy import select, func

    member_id = _get_member_from_user(current_user)

    query = select(Order).where(Order.member_id == member_id)
    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    orders = list(result.scalars().all())

    return ListResponse(
        data=orders,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.get("/member/notifications", response_model=ListResponse[MiniNotificationItem])
async def get_my_notifications(
    is_read: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的通知"""
    from sqlalchemy import select, func

    query = select(Notification).where(Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    notifications = list(result.scalars().all())

    data = [
        MiniNotificationItem(
            id=n.id,
            notification_type=n.notification_type.value if n.notification_type else "system",
            title=n.title,
            content=n.content,
            is_read=n.is_read,
            link=n.link,
            created_at=n.created_at,
        )
        for n in notifications
    ]

    return ListResponse(
        data=data,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.put("/member/notifications/{notification_id}/read", response_model=BaseResponse)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记通知已读"""
    from sqlalchemy import select

    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在",
        )

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.flush()

    return BaseResponse(message="标记成功")


@router.put("/member/notifications/read-all", response_model=BaseResponse)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """全部标记已读"""
    from sqlalchemy import select, update

    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.flush()

    return BaseResponse(message="全部标记成功")


@router.get("/checkin/qrcode")
async def get_checkin_qrcode(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    生成签到二维码
    二维码内容为签名的 token，包含会员ID和时间戳，有效期5分钟
    """
    import io
    import base64
    import time
    import hashlib
    import hmac

    member_id = _get_member_from_user(current_user)

    # 生成签名 token
    timestamp = str(int(time.time()))
    payload = f"{member_id}:{timestamp}"
    secret = "fitai_checkin_secret"  # 生产环境应从配置读取
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    token = f"{payload}:{signature}"

    # 生成二维码
    try:
        import qrcode
        from qrcode.image.pil import PilImage

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(f"fitai://checkin?token={token}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="#1a1a2e", back_color="white")

        # 转为 base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return BaseResponse(data={
            "qrcode": f"data:image/png;base64,{img_base64}",
            "token": token,
            "expires_in": 300,
        })
    except ImportError:
        # qrcode 库不可用时返回占位
        return BaseResponse(data={
            "qrcode": "",
            "token": token,
            "expires_in": 300,
            "message": "二维码生成库未安装",
        })
