"""
Pydantic Schema - 系统设置
"""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    contact_name: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)
    settings: Optional[Any] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    plan: str
    status: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    settings: Optional[Any] = None
    is_active: bool
    trial_ends_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreateByAdmin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=6)
    role: str = Field("receptionist")


class UserUpdateByAdmin(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserManageResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    is_superuser: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
