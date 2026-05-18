from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional, List, Dict

class CourseCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

class CourseCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClassroomCreate(BaseModel):
    name: str
    capacity: Optional[int] = 20
    equipment: Optional[Dict] = None

class ClassroomResponse(BaseModel):
    id: int
    name: str
    capacity: int
    equipment: Optional[Dict]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    name: str
    category_id: int
    course_type: str
    duration: int
    price: float
    description: Optional[str] = None
    max_capacity: Optional[int] = 20

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    course_type: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    max_capacity: Optional[int] = None
    is_active: Optional[bool] = None

class CourseResponse(BaseModel):
    id: int
    name: str
    category: Optional[CourseCategoryResponse]
    course_type: str
    duration: int
    price: float
    description: Optional[str]
    max_capacity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ScheduleCreate(BaseModel):
    course_id: int
    classroom_id: int
    coach_id: int
    date: date
    start_time: time
    end_time: time
    max_capacity: Optional[int] = None

class ScheduleUpdate(BaseModel):
    status: Optional[str] = None
    max_capacity: Optional[int] = None

class ScheduleResponse(BaseModel):
    id: int
    course: CourseResponse
    classroom: ClassroomResponse
    coach_id: int
    date: date
    start_time: time
    end_time: time
    status: str
    max_capacity: int
    current_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True