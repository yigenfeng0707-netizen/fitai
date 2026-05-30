"""
API - 小程序课程/预约
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.member import Member
from backend.models.course import Course, CourseSchedule, CourseType
from backend.models.booking import Booking, BookingStatus
from backend.schemas.mini import (
    MiniCourseItem,
    MiniScheduleItem,
    MiniCoachItem,
    MiniBookingItem,
    MiniBookingCreate,
)
from backend.schemas.common import BaseResponse, ListResponse

router = APIRouter(prefix="/mini", tags=["小程序-课程"])


def _get_member_from_user(user: User) -> int:
    """从用户获取关联的会员ID"""
    if not user.member_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="当前用户未关联会员信息",
        )
    return user.member_id


@router.get("/courses", response_model=ListResponse[MiniCourseItem])
async def get_courses(
    course_type: Optional[CourseType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程列表（仅活跃课程）"""
    from sqlalchemy import select, func

    query = select(Course).where(
        Course.organization_id == current_user.organization_id,
        Course.is_active == True,  # noqa: E712
    )
    if course_type:
        query = query.where(Course.course_type == course_type)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.offset(skip).limit(limit).order_by(Course.created_at.desc())
    result = await db.execute(query)
    courses = list(result.scalars().all())

    data = []
    for course in courses:
        coach_name = None
        if course.coach_id:
            from backend.models.coach import Coach
            coach_result = await db.execute(
                select(Coach.name).where(Coach.id == course.coach_id)
            )
            coach_name = coach_result.scalar_one_or_none()

        data.append(MiniCourseItem(
            id=course.id,
            name=course.name,
            course_type=course.course_type.value,
            description=course.description,
            duration_minutes=course.duration_minutes,
            price=course.price,
            coach_name=coach_name,
            max_attendees=course.max_attendees,
        ))

    return ListResponse(
        data=data,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.get("/courses/{course_id}", response_model=MiniCourseItem)
async def get_course_detail(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程详情"""
    from sqlalchemy import select

    result = await db.execute(
        select(Course).where(
            Course.id == course_id,
            Course.organization_id == current_user.organization_id,
        )
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在",
        )

    coach_name = None
    if course.coach_id:
        from backend.models.coach import Coach
        coach_result = await db.execute(
            select(Coach.name).where(Coach.id == course.coach_id)
        )
        coach_name = coach_result.scalar_one_or_none()

    return MiniCourseItem(
        id=course.id,
        name=course.name,
        course_type=course.course_type.value,
        description=course.description,
        duration_minutes=course.duration_minutes,
        price=course.price,
        coach_name=coach_name,
        max_attendees=course.max_attendees,
    )


@router.get("/schedules", response_model=ListResponse[MiniScheduleItem])
async def get_schedules(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD"),
    course_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取排课列表（按日期）"""
    from sqlalchemy import select, func

    member_id = current_user.member_id

    query = select(CourseSchedule).where(
        CourseSchedule.organization_id == current_user.organization_id,
        CourseSchedule.status == "scheduled",
    )

    # 按日期过滤
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            start_of_day = datetime.combine(filter_date, datetime.min.time())
            end_of_day = start_of_day + timedelta(days=1)
            query = query.where(
                CourseSchedule.start_time >= start_of_day,
                CourseSchedule.start_time < end_of_day,
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD",
            )

    if course_id:
        query = query.where(CourseSchedule.course_id == course_id)

    # 只返回未来的排课
    query = query.where(CourseSchedule.start_time >= datetime.now(timezone.utc))

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(CourseSchedule.start_time.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    schedules = list(result.scalars().all())

    # 查询当前用户已有的预约
    booked_schedule_ids = set()
    if member_id:
        booking_result = await db.execute(
            select(Booking.schedule_id).where(
                Booking.member_id == member_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            )
        )
        for row in booking_result:
            booked_schedule_ids.add(row[0])

    data = []
    for schedule in schedules:
        # 获取课程信息
        course_result = await db.execute(
            select(Course).where(Course.id == schedule.course_id)
        )
        course = course_result.scalar_one_or_none()

        course_name = course.name if course else ""
        max_attendees = course.max_attendees if course else 10
        coach_name = None

        if course and course.coach_id:
            from backend.models.coach import Coach
            coach_result = await db.execute(
                select(Coach.name).where(Coach.id == course.coach_id)
            )
            coach_name = coach_result.scalar_one_or_none()

        data.append(MiniScheduleItem(
            id=schedule.id,
            course_id=schedule.course_id,
            course_name=course_name,
            coach_name=coach_name,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            enrolled_count=schedule.enrolled_count,
            max_attendees=max_attendees,
            available_slots=max(0, max_attendees - schedule.enrolled_count),
            is_booked=schedule.id in booked_schedule_ids,
        ))

    return ListResponse(
        data=data,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.get("/coaches", response_model=ListResponse[MiniCoachItem])
async def get_coaches(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教练列表"""
    from sqlalchemy import select, func
    from backend.models.coach import Coach

    query = select(Coach).where(
        Coach.organization_id == current_user.organization_id,
    )

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    coaches = list(result.scalars().all())

    data = [
        MiniCoachItem(
            id=c.id,
            name=c.name,
            phone=c.phone,
            specialty=c.specialty if hasattr(c, "specialty") else None,
            avatar=c.avatar if hasattr(c, "avatar") else None,
        )
        for c in coaches
    ]

    return ListResponse(
        data=data,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.post("/bookings", response_model=MiniBookingItem)
async def create_booking(
    obj_in: MiniBookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    预约课程
    检查: 排课存在、未满员、会员卡有效、未重复预约
    """
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)

    # 检查排课是否存在
    schedule_result = await db.execute(
        select(CourseSchedule).where(CourseSchedule.id == obj_in.schedule_id)
    )
    schedule = schedule_result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="排课不存在",
        )

    if schedule.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该排课已取消或结束",
        )

    # 检查课程是否已满
    course_result = await db.execute(
        select(Course).where(Course.id == schedule.course_id)
    )
    course = course_result.scalar_one_or_none()

    if course and schedule.enrolled_count >= course.max_attendees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="课程已满员",
        )

    # 检查会员卡是否有效
    member_result = await db.execute(
        select(Member).where(Member.id == member_id)
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会员信息不存在",
        )

    if member.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会员卡已失效，请续费",
        )

    # 检查是否已预约
    existing_booking = await db.execute(
        select(Booking).where(
            Booking.member_id == member_id,
            Booking.schedule_id == obj_in.schedule_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
    )
    if existing_booking.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已预约该课程",
        )

    # 创建预约
    booking = Booking(
        member_id=member_id,
        schedule_id=obj_in.schedule_id,
        status=BookingStatus.CONFIRMED,
        organization_id=current_user.organization_id,
    )
    db.add(booking)

    # 更新已报名人数
    schedule.enrolled_count = (schedule.enrolled_count or 0) + 1
    await db.flush()

    # 获取教练名称
    coach_name = None
    if course and course.coach_id:
        from backend.models.coach import Coach
        coach_result = await db.execute(
            select(Coach.name).where(Coach.id == course.coach_id)
        )
        coach_name = coach_result.scalar_one_or_none()

    return MiniBookingItem(
        id=booking.id,
        schedule_id=booking.schedule_id,
        course_name=course.name if course else "",
        coach_name=coach_name,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        status=booking.status.value,
        check_in_time=None,
        can_cancel=True,
        can_checkin=True,
    )


@router.delete("/bookings/{booking_id}", response_model=BaseResponse)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取消预约
    检查: 预约存在、属于当前用户、未取消/签到
    """
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)

    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在",
        )

    if booking.member_id != member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此预约",
        )

    if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态不允许取消: {booking.status.value}",
        )

    # 更新预约状态
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)
    booking.cancelled_by = current_user.id
    booking.cancel_reason = "用户自行取消"

    # 减少已报名人数
    schedule_result = await db.execute(
        select(CourseSchedule).where(CourseSchedule.id == booking.schedule_id)
    )
    schedule = schedule_result.scalar_one_or_none()
    if schedule and schedule.enrolled_count > 0:
        schedule.enrolled_count -= 1

    await db.flush()

    return BaseResponse(message="取消成功")


@router.post("/bookings/{booking_id}/checkin", response_model=MiniBookingItem)
async def check_in(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    签到
    检查: 预约存在、属于当前用户、状态为已预约
    """
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)

    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在",
        )

    if booking.member_id != member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此预约",
        )

    if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态不允许签到: {booking.status.value}",
        )

    # 更新签到状态
    booking.status = BookingStatus.CHECKED_IN
    booking.check_in_time = datetime.now(timezone.utc)
    booking.check_in_method = "mini_program"
    await db.flush()

    # 获取排课和课程信息
    schedule_result = await db.execute(
        select(CourseSchedule).where(CourseSchedule.id == booking.schedule_id)
    )
    schedule = schedule_result.scalar_one_or_none()

    course_name = ""
    coach_name = None
    if schedule:
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

    return MiniBookingItem(
        id=booking.id,
        schedule_id=booking.schedule_id,
        course_name=course_name,
        coach_name=coach_name,
        start_time=schedule.start_time if schedule else datetime.now(timezone.utc),
        end_time=schedule.end_time if schedule else datetime.now(timezone.utc),
        status=booking.status.value,
        check_in_time=booking.check_in_time,
        can_cancel=False,
        can_checkin=False,
    )


@router.get("/bookings/today", response_model=ListResponse[MiniBookingItem])
async def get_today_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取今日预约"""
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    result = await db.execute(
        select(Booking).where(
            Booking.member_id == member_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
        )
    )
    bookings = list(result.scalars().all())

    # 过滤今日排课
    data = []
    for booking in bookings:
        schedule_result = await db.execute(
            select(CourseSchedule).where(CourseSchedule.id == booking.schedule_id)
        )
        schedule = schedule_result.scalar_one_or_none()

        if not schedule:
            continue

        if not (today_start <= schedule.start_time < today_end):
            continue

        course_name = ""
        coach_name = None
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
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            status=booking.status.value,
            check_in_time=booking.check_in_time,
            can_cancel=can_cancel,
            can_checkin=can_checkin,
        ))

    return ListResponse(
        data=data,
        total=len(data),
        page=1,
        page_size=len(data),
    )
