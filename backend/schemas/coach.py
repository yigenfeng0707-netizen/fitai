"""
Pydantic Schema - 教练
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from pydantic import BaseModel, Field


class CoachBase(BaseModel):
    """教练基础字段"""
    name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=11, max_length=20)
    email: Optional[str] = None
    specialization: Optional[str] = None
    introduction: Optional[str] = None
    is_active: bool = True


class CoachCreate(CoachBase):
    """创建教练"""
    certificates: Optional[list[str]] = None
    work_schedule: Optional[dict] = None


class CoachUpdate(BaseModel):
    """更新教练"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, min_length=11, max_length=20)
    email: Optional[str] = None
    specialization: Optional[str] = None
    introduction: Optional[str] = None
    certificates: Optional[list[str]] = None
    work_schedule: Optional[dict] = None
    is_active: Optional[bool] = None


class CoachResponse(CoachBase):
    """教练响应"""
    id: int
    certificates: Optional[list[str]] = None
    work_schedule: Optional[dict] = None
    total_hours: float
    total_students: int
    avg_rating: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True