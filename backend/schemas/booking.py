"""
Pydantic Schema - 预约
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from backend.models.booking import BookingStatus


class BookingCreate(BaseModel):
    """创建预约"""
    member_id: int
    schedule_id: int
    notes: Optional[str] = None


class BookingUpdate(BaseModel):
    """更新预约"""
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    """预约响应"""
    id: int
    organization_id: int
    member_id: int
    schedule_id: int
    status: BookingStatus
    check_in_time: Optional[datetime] = None
    check_in_method: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[int] = None
    cancel_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class BookingCheckIn(BaseModel):
    """签到"""
    check_in_method: str = "manual"  # qrcode, manual
    notes: Optional[str] = None