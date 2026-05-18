from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class MemberLevelCreate(BaseModel):
    name: str
    min_points: Optional[int] = 0
    discount: Optional[float] = 1.0
    privileges: Optional[Dict] = None

class MemberLevelResponse(BaseModel):
    id: int
    name: str
    min_points: int
    discount: float
    privileges: Optional[Dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MemberCardCreate(BaseModel):
    card_no: str
    card_type: str
    total_hours: Optional[float] = None
    balance: Optional[float] = 0
    start_date: datetime
    end_date: Optional[datetime] = None

class MemberCardResponse(BaseModel):
    id: int
    card_no: str
    member_id: int
    card_type: str
    total_hours: Optional[float]
    used_hours: float
    balance: float
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BodyTestRecordCreate(BaseModel):
    test_date: datetime
    height: Optional[float] = None
    weight: Optional[float] = None
    body_fat_rate: Optional[float] = None
    muscle_rate: Optional[float] = None
    bmi: Optional[float] = None
    waist: Optional[float] = None
    hip: Optional[float] = None
    notes: Optional[str] = None

class BodyTestRecordResponse(BaseModel):
    id: int
    member_id: int
    test_date: datetime
    height: Optional[float]
    weight: Optional[float]
    body_fat_rate: Optional[float]
    muscle_rate: Optional[float]
    bmi: Optional[float]
    waist: Optional[float]
    hip: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class MemberCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    level_id: Optional[int] = 1
    points: Optional[int] = 0
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    level_id: Optional[int] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    freeze_until: Optional[datetime] = None
    notes: Optional[str] = None

class MemberResponse(BaseModel):
    id: int
    member_no: str
    name: str
    phone: str
    email: Optional[str]
    avatar: Optional[str]
    level: Optional[MemberLevelResponse]
    points: int
    tags: Optional[List[str]]
    status: str
    freeze_until: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True