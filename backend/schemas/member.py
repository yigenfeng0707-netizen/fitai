"""
Pydantic Schema - 会员
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend.models.member import CardType, MemberStatus


class MemberBase(BaseModel):
    """会员基础字段"""
    name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=11, max_length=20)
    email: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[datetime] = None


class MemberCreate(MemberBase):
    """创建会员"""
    coach_id: Optional[int] = None
    initial_card_type: Optional[CardType] = None
    initial_card_count: Optional[int] = Field(None, ge=1)  # 次卡初始次数
    initial_card_balance: Optional[float] = Field(None, ge=0)  # 储值卡初始余额


class MemberUpdate(BaseModel):
    """更新会员"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, min_length=11, max_length=20)
    email: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[datetime] = None
    card_type: Optional[CardType] = None
    card_start_date: Optional[datetime] = None
    card_end_date: Optional[datetime] = None
    card_remaining_count: Optional[int] = Field(None, ge=0)
    card_balance: Optional[float] = Field(None, ge=0)
    level: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[MemberStatus] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    coach_id: Optional[int] = None


class MemberResponse(MemberBase):
    """会员响应"""
    id: int
    card_type: Optional[CardType] = None
    card_start_date: Optional[datetime] = None
    card_end_date: Optional[datetime] = None
    card_remaining_count: Optional[int] = None
    card_balance: Optional[float] = None
    level: int
    total_consumption: float
    status: MemberStatus
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    coach_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True