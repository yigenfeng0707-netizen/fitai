"""
CRUD - 课程
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.models.course import Course, CourseSchedule, CourseType
from backend.models.coach import Coach
from backend.schemas.course import CourseCreate, CourseUpdate, CourseScheduleCreate


class CourseCRUD:
    """课程 CRUD"""
    
    @staticmethod
    async def get(db: AsyncSession, course_id: int) -> Optional[Course]:
        """获取课程"""
        result = await db.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: CourseCreate, organization_id: int = 1) -> Course:
        """创建课程"""
        course = Course(
            name=obj_in.name,
            description=obj_in.description,
            course_type=obj_in.course_type,
            duration_minutes=obj_in.duration_minutes,
            room=obj_in.room,
            price=obj_in.price,
            package_price=obj_in.package_price,
            coach_id=obj_in.coach_id,
            is_active=obj_in.is_active,
            max_attendees=obj_in.max_attendees,
            organization_id=organization_id,
        )
        
        db.add(course)
        await db.flush()
        return course
    
    @staticmethod
    async def update(db: AsyncSession, course: Course, obj_in: CourseUpdate) -> Course:
        """更新课程"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(course, field, value)
        
        await db.flush()
        return course
    
    @staticmethod
    async def delete(db: AsyncSession, course: Course) -> None:
        """删除课程"""
        await db.delete(course)
    
    @staticmethod
    async def get_list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        course_type: Optional[CourseType] = None,
        is_active: Optional[bool] = None,
        coach_id: Optional[int] = None,
        organization_id: int = 1,
    ) -> tuple[list[Course], int]:
        """获取课程列表"""
        from sqlalchemy import func
        
        query = select(Course).where(Course.organization_id == organization_id)
        
        if course_type:
            query = query.where(Course.course_type == course_type)
        
        if is_active is not None:
            query = query.where(Course.is_active == is_active)
        
        if coach_id:
            query = query.where(Course.coach_id == coach_id)
        
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        
        return result.scalars().all(), total
    
    @staticmethod
    async def create_schedule(db: AsyncSession, obj_in: CourseScheduleCreate, organization_id: int = 1) -> CourseSchedule:
        """创建课程排期"""
        schedule = CourseSchedule(
            course_id=obj_in.course_id,
            start_time=obj_in.start_time,
            end_time=obj_in.end_time,
            status="scheduled",
            notes=obj_in.notes,
            organization_id=organization_id,
        )
        
        db.add(schedule)
        await db.flush()
        return schedule
    
    @staticmethod
    async def get_schedule(db: AsyncSession, schedule_id: int) -> Optional[CourseSchedule]:
        """获取课程排期"""
        result = await db.execute(
            select(CourseSchedule).where(CourseSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_schedules_by_course(
        db: AsyncSession,
        course_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: int = 1,
    ) -> list[CourseSchedule]:
        """获取课程排期列表"""
        query = select(CourseSchedule).where(
            CourseSchedule.course_id == course_id,
            CourseSchedule.organization_id == organization_id,
        )
        
        if start_date:
            query = query.where(CourseSchedule.start_time >= start_date)
        if end_date:
            query = query.where(CourseSchedule.start_time <= end_date)
        
        result = await db.execute(query.order_by(CourseSchedule.start_time))
        return list(result.scalars().all())

    @staticmethod
    async def update_schedule(db: AsyncSession, schedule: CourseSchedule, obj_in: dict) -> CourseSchedule:
        """更新课程排期"""
        for field, value in obj_in.items():
            if value is not None:
                setattr(schedule, field, value)
        await db.flush()
        return schedule

    @staticmethod
    async def delete_schedule(db: AsyncSession, schedule: CourseSchedule) -> None:
        """删除课程排期"""
        await db.delete(schedule)

    @staticmethod
    async def get_schedules_by_date_range(
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        coach_id: Optional[int] = None,
        organization_id: int = 1,
    ) -> list[dict]:
        """按日期范围获取排期（含课程和教练信息）"""
        from sqlalchemy.orm import joinedload

        query = (
            select(CourseSchedule)
            .options(joinedload(CourseSchedule.course))
            .where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.start_time >= start_date,
                CourseSchedule.start_time <= end_date,
            )
        )
        if coach_id:
            query = query.where(CourseSchedule.course.has(Course.coach_id == coach_id))

        result = await db.execute(query.order_by(CourseSchedule.start_time))
        schedules = result.unique().scalars().all()

        items = []
        for s in schedules:
            course = s.course
            item = {
                "id": s.id,
                "course_id": s.course_id,
                "course_name": course.name if course else "",
                "course_type": course.course_type.value if course else "",
                "coach_id": course.coach_id if course else None,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "status": s.status,
                "enrolled_count": s.enrolled_count,
                "max_capacity": course.max_attendees if course else 0,
                "room": course.room if course and course.room else "",
                "notes": s.notes,
                "created_at": s.created_at,
            }
            items.append(item)

        return items

    @staticmethod
    async def batch_create_schedules(
        db: AsyncSession,
        items: list[dict],
        organization_id: int = 1,
    ) -> list[CourseSchedule]:
        """批量创建排期（用于每周重复排课）"""
        schedules = []
        for item in items:
            schedule = CourseSchedule(
                course_id=item["course_id"],
                start_time=item["start_time"],
                end_time=item["end_time"],
                status="scheduled",
                notes=item.get("notes"),
                organization_id=organization_id,
            )
            db.add(schedule)
            schedules.append(schedule)

        await db.flush()
        return schedules