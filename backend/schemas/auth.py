"""
Pydantic Schema - 认证
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend.core.permissions import Role


class UserLogin(BaseModel):
    """用户登录"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=6)
    role: Role = Field(default=Role.RECEPTIONIST)


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool
    organization_id: int = 1
    last_login_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}