from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BookingCreate(BaseModel):
    schedule_id: int
    member_id: int
    notes: Optional[str] = None

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: int
    schedule_id: int
    member_id: int
    status: str
    booked_at: datetime
    canceled_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True

class AttendanceCreate(BaseModel):
    booking_id: int

class AttendanceResponse(BaseModel):
    id: int
    booking_id: int
    check_in_time: datetime
    check_out_time: Optional[datetime]
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True