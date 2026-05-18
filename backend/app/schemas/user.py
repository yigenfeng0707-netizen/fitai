from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = 2
    store_id: Optional[int] = 1

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    role_id: int
    store_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True