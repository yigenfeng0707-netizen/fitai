from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional, List, Dict

class CoachCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    qualifications: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    hourly_rate: Optional[float] = None

class CoachUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    qualifications: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    status: Optional[str] = None

class CoachResponse(BaseModel):
    id: int
    coach_no: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    avatar: Optional[str]
    qualifications: Optional[List[str]]
    specialties: Optional[List[str]]
    hourly_rate: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CoachScheduleCreate(BaseModel):
    coach_id: int
    day_of_week: int
    start_time: time
    end_time: time

class CoachScheduleResponse(BaseModel):
    id: int
    coach_id: int
    day_of_week: int
    start_time: time
    end_time: time
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeachingRecordCreate(BaseModel):
    coach_id: int
    schedule_id: int
    date: date
    duration: Optional[int] = None
    attendees: Optional[int] = None
    rating: Optional[int] = None
    notes: Optional[str] = None

class TeachingRecordResponse(BaseModel):
    id: int
    coach_id: int
    schedule_id: int
    date: date
    duration: Optional[int]
    attendees: Optional[int]
    rating: Optional[int]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True