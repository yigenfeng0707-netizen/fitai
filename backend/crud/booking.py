"""
CRUD - 预约
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.models.booking import Booking, BookingStatus
from backend.models.course import CourseSchedule
from backend.schemas.booking import BookingCreate, BookingUpdate


class BookingCRUD:
    """预约 CRUD"""
    
    @staticmethod
    async def get(db: AsyncSession, booking_id: int) -> Optional[Booking]:
        """获取预约"""
        result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: BookingCreate, organization_id: int = 1) -> Booking:
        """创建预约"""
        from .course import CourseCRUD  # 延迟导入避免循环依赖
        
        # 检查课程排期是否还有名额
        schedule = await CourseCRUD.get_schedule(db, obj_in.schedule_id)
        if not schedule:
            raise ValueError("课程排期不存在")
        
        # 通过 course_id 直接查询课程，避免懒加载问题
        from sqlalchemy import select
        from backend.models.course import Course
        result = await db.execute(select(Course).where(Course.id == schedule.course_id))
        course = result.scalar_one_or_none()
        if not course:
            raise ValueError("课程不存在")
        
        # 检查是否已满
        if schedule.enrolled_count >= course.max_attendees:
            raise ValueError("课程已满")
        
        booking = Booking(
            member_id=obj_in.member_id,
            schedule_id=obj_in.schedule_id,
            status=BookingStatus.PENDING,
            notes=obj_in.notes,
            organization_id=organization_id,
        )
        
        db.add(booking)
        await db.flush()
        
        # 增加已报名人数
        schedule.enrolled_count += 1
        
        return booking
    
    @staticmethod
    async def update(db: AsyncSession, booking: Booking, obj_in: BookingUpdate) -> Booking:
        """更新预约"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(booking, field, value)
        
        await db.flush()
        return booking
    
    @staticmethod
    async def cancel(db: AsyncSession, booking: Booking, cancelled_by: int, reason: Optional[str] = None) -> Booking:
        """取消预约"""
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancelled_by = cancelled_by
        booking.cancel_reason = reason
        
        # 减少已报名人数
        if booking.schedule:
            booking.schedule.enrolled_count = max(0, booking.schedule.enrolled_count - 1)
        
        await db.flush()
        return booking
    
    @staticmethod
    async def check_in(db: AsyncSession, booking: Booking, method: str = "manual") -> Booking:
        """签到"""
        booking.status = BookingStatus.CHECKED_IN
        booking.check_in_time = datetime.utcnow()
        booking.check_in_method = method
        
        await db.flush()
        return booking
    
    @staticmethod
    async def get_list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        member_id: Optional[int] = None,
        schedule_id: Optional[int] = None,
        status: Optional[BookingStatus] = None,
        organization_id: int = 1,
    ) -> tuple[list[Booking], int]:
        """获取预约列表"""
        from sqlalchemy import func
        
        query = select(Booking).where(Booking.organization_id == organization_id)
        
        if member_id:
            query = query.where(Booking.member_id == member_id)
        if schedule_id:
            query = query.where(Booking.schedule_id == schedule_id)
        if status:
            query = query.where(Booking.status == status)
        
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        
        query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        
        return result.scalars().all(), total
    
    @staticmethod
    async def get_today_bookings(db: AsyncSession, date: Optional[datetime] = None, organization_id: int = 1) -> list[Booking]:
        """获取今日预约"""
        if not date:
            date = datetime.utcnow()
        
        start = date.replace(hour=0, minute=0, second=0)
        end = date.replace(hour=23, minute=59, second=59)
        
        query = select(Booking).join(CourseSchedule).where(
            CourseSchedule.start_time >= start,
            CourseSchedule.start_time <= end,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
            Booking.organization_id == organization_id,
        )
        
        result = await db.execute(query.order_by(CourseSchedule.start_time))
        return list(result.scalars().all())

    @staticmethod
    async def get_today_checkin_data(
        db: AsyncSession,
        date: Optional[datetime] = None,
        organization_id: int = 1,
    ) -> list[dict]:
        """获取今日签到数据（含会员名、课程名、排期信息）"""
        if not date:
            date = datetime.utcnow()

        start = date.replace(hour=0, minute=0, second=0)
        end = date.replace(hour=23, minute=59, second=59)

        query = (
            select(Booking)
            .options(
                joinedload(Booking.member),
                joinedload(Booking.schedule).joinedload(CourseSchedule.course),
            )
            .join(CourseSchedule)
            .where(
                CourseSchedule.start_time >= start,
                CourseSchedule.start_time <= end,
                Booking.organization_id == organization_id,
            )
        )

        result = await db.execute(query.order_by(CourseSchedule.start_time))
        bookings = result.unique().scalars().all()

        items = []
        for b in bookings:
            schedule = b.schedule
            course = schedule.course if schedule else None
            member = b.member
            items.append({
                "id": b.id,
                "member_id": b.member_id,
                "member_name": member.name if member else "",
                "member_phone": member.phone if member else "",
                "schedule_id": b.schedule_id,
                "course_name": course.name if course else "",
                "course_type": course.course_type.value if course else "",
                "start_time": schedule.start_time if schedule else None,
                "end_time": schedule.end_time if schedule else None,
                "status": b.status.value,
                "check_in_time": b.check_in_time,
                "check_in_method": b.check_in_method,
                "notes": b.notes,
                "created_at": b.created_at,
            })

        return items

    @staticmethod
    async def get_today_stats(
        db: AsyncSession,
        date: Optional[datetime] = None,
        organization_id: int = 1,
    ) -> dict:
        """获取今日签到统计"""
        items = await BookingCRUD.get_today_checkin_data(db, date, organization_id)

        total = len(items)
        checked_in = sum(1 for i in items if i["status"] == "checked_in")
        pending = sum(1 for i in items if i["status"] == "pending")
        confirmed = sum(1 for i in items if i["status"] == "confirmed")
        cancelled = sum(1 for i in items if i["status"] == "cancelled")
        no_show = sum(1 for i in items if i["status"] == "no_show")

        # 按排期分组
        schedule_groups: dict[int, dict] = {}
        for i in items:
            sid = i["schedule_id"]
            if sid not in schedule_groups:
                schedule_groups[sid] = {
                    "schedule_id": sid,
                    "course_name": i["course_name"],
                    "start_time": i["start_time"],
                    "end_time": i["end_time"],
                    "enrolled_count": 0,
                    "checked_in_count": 0,
                    "bookings": [],
                }
            schedule_groups[sid]["bookings"].append(i)
            schedule_groups[sid]["enrolled_count"] += 1
            if i["status"] == "checked_in":
                schedule_groups[sid]["checked_in_count"] += 1

        return {
            "total": total,
            "checked_in": checked_in,
            "pending": pending,
            "confirmed": confirmed,
            "cancelled": cancelled,
            "no_show": no_show,
            "schedules": list(schedule_groups.values()),
        }