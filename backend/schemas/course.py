"""
Pydantic Schema - 课程
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend.models.course import CourseType


class CourseBase(BaseModel):
    """课程基础字段"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    course_type: CourseType
    duration_minutes: int = Field(default=60, ge=15, le=180)
    room: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    package_price: Optional[float] = Field(None, ge=0)
    coach_id: Optional[int] = None
    is_active: bool = True
    max_attendees: int = Field(default=10, ge=1, le=50)


class CourseCreate(CourseBase):
    """创建课程"""
    pass


class CourseUpdate(BaseModel):
    """更新课程"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    course_type: Optional[CourseType] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    room: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    package_price: Optional[float] = Field(None, ge=0)
    coach_id: Optional[int] = None
    is_active: Optional[bool] = None
    max_attendees: Optional[int] = Field(None, ge=1, le=50)


class CourseResponse(CourseBase):
    """课程响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CourseScheduleCreate(BaseModel):
    """创建课程排期"""
    course_id: int
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None


class CourseScheduleUpdate(BaseModel):
    """更新课程排期"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CourseScheduleResponse(BaseModel):
    """课程排期响应"""
    id: int
    course_id: int
    course_name: str = ""
    course_type: str = ""
    coach_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    status: str
    enrolled_count: int
    max_capacity: int = 0
    room: str = ""
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True