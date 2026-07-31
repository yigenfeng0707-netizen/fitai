"""
API - 课程
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.course import Course, CourseType, CourseSchedule
from backend.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse,
    CourseScheduleCreate, CourseScheduleUpdate, CourseScheduleResponse
)
from backend.models.auth import User
from backend.schemas.common import BaseResponse, ListResponse

router = APIRouter()


@router.post("/", response_model=CourseResponse)
async def create_course(
    obj_in: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建课程"""
    from backend.crud.course import CourseCRUD
    course = await CourseCRUD.create(db, obj_in, organization_id=current_user.organization_id)
    return course


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程详情"""
    from backend.crud.course import CourseCRUD
    course = await CourseCRUD.get(db, course_id)
    if not course or course.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在",
        )
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    obj_in: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新课程"""
    from backend.crud.course import CourseCRUD
    course = await CourseCRUD.get(db, course_id)
    if not course or course.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在",
        )
    
    course = await CourseCRUD.update(db, course, obj_in)
    return course


@router.delete("/{course_id}", response_model=BaseResponse)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除课程"""
    from backend.crud.course import CourseCRUD
    course = await CourseCRUD.get(db, course_id)
    if not course or course.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在",
        )
    
    await CourseCRUD.delete(db, course)
    return BaseResponse(message="删除成功")


@router.get("/", response_model=ListResponse[CourseResponse])
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    course_type: Optional[CourseType] = None,
    is_active: Optional[bool] = None,
    coach_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程列表"""
    from backend.crud.course import CourseCRUD
    courses, total = await CourseCRUD.get_list(
        db, skip=skip, limit=limit,
        course_type=course_type, is_active=is_active, coach_id=coach_id,
        organization_id=current_user.organization_id,
    )
    
    return ListResponse(
        data=courses,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.post("/schedules/", response_model=CourseScheduleResponse)
async def create_schedule(
    obj_in: CourseScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建课程排期"""
    from backend.crud.course import CourseCRUD
    course = await CourseCRUD.get(db, obj_in.course_id)
    if not course or course.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在",
        )

    schedule = await CourseCRUD.create_schedule(db, obj_in, organization_id=current_user.organization_id)
    return {
        "id": schedule.id,
        "course_id": schedule.course_id,
        "course_name": course.name,
        "course_type": course.course_type.value,
        "coach_id": course.coach_id,
        "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "status": schedule.status,
        "enrolled_count": schedule.enrolled_count,
        "max_capacity": course.max_attendees,
        "room": course.room or "",
        "notes": schedule.notes,
        "created_at": schedule.created_at,
    }


@router.get("/schedules/{schedule_id}", response_model=CourseScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程排期详情"""
    from backend.crud.course import CourseCRUD
    schedule = await CourseCRUD.get_schedule(db, schedule_id)
    if not schedule or schedule.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程排期不存在",
        )
    return schedule


@router.get("/schedules/", response_model=ListResponse[CourseScheduleResponse])
async def get_schedules(
    course_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    coach_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程排期列表"""
    from backend.crud.course import CourseCRUD
    if start_date and end_date:
        items = await CourseCRUD.get_schedules_by_date_range(
            db, start_date, end_date,
            coach_id=coach_id,
            organization_id=current_user.organization_id,
        )
        total = len(items)
        data = items[skip:skip + limit] if limit < total else items
        return ListResponse(
            data=data,
            total=total,
            page=skip // limit + 1 if skip else 1,
            page_size=limit,
        )

    if course_id:
        schedules = await CourseCRUD.get_schedules_by_course(
            db, course_id, start_date, end_date,
            organization_id=current_user.organization_id,
        )
        total = len(schedules)
    else:
        from sqlalchemy import select, func
        query = select(CourseSchedule).where(
            CourseSchedule.organization_id == current_user.organization_id,
        )
        if start_date:
            query = query.where(CourseSchedule.start_time >= start_date)
        if end_date:
            query = query.where(CourseSchedule.start_time <= end_date)
        if coach_id:
            query = query.where(CourseSchedule.course.has(Course.coach_id == coach_id))
        
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        
        query = query.offset(skip).limit(limit).order_by(CourseSchedule.start_time)
        result = await db.execute(query)
        schedules = list(result.scalars().all())
    
    return ListResponse(
        data=schedules,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.put("/schedules/{schedule_id}", response_model=CourseScheduleResponse)
async def update_schedule(
    schedule_id: int,
    obj_in: CourseScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新课程排期"""
    from backend.crud.course import CourseCRUD
    schedule = await CourseCRUD.get_schedule(db, schedule_id)
    if not schedule or schedule.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程排期不存在",
        )

    update_data = obj_in.model_dump(exclude_unset=True)
    schedule = await CourseCRUD.update_schedule(db, schedule, update_data)
    return schedule


@router.delete("/schedules/{schedule_id}", response_model=BaseResponse)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除课程排期"""
    from backend.crud.course import CourseCRUD
    schedule = await CourseCRUD.get_schedule(db, schedule_id)
    if not schedule or schedule.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程排期不存在",
        )

    await CourseCRUD.delete_schedule(db, schedule)
    return BaseResponse(message="删除成功")


class BatchScheduleItem(BaseModel):
    course_id: int
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None


class BatchScheduleCreate(BaseModel):
    schedules: list[BatchScheduleItem]


@router.post("/schedules/batch", response_model=BaseResponse)
async def batch_create_schedules(
    obj_in: BatchScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建排期"""
    from backend.crud.course import CourseCRUD
    items = [item.model_dump() for item in obj_in.schedules]
    count = len(await CourseCRUD.batch_create_schedules(
        db, items, organization_id=current_user.organization_id,
    ))
    return BaseResponse(message=f"成功创建 {count} 个排期")