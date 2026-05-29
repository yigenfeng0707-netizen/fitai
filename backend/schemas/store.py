"""
Pydantic Schema - 门店
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class StoreBase(BaseModel):
    name: str = Field(..., max_length=100)
    address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    manager_id: Optional[int] = None
    is_active: bool = True
    business_hours: Optional[Any] = None
    facilities: Optional[Any] = None
    max_capacity: int = 0
    settings: Optional[Any] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class StoreCreate(StoreBase):
    code: Optional[str] = Field(None, max_length=50)


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None
    business_hours: Optional[Any] = None
    facilities: Optional[Any] = None
    max_capacity: Optional[int] = None
    settings: Optional[Any] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class StoreResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    phone: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: bool
    business_hours: Optional[Any] = None
    facilities: Optional[Any] = None
    max_capacity: int
    settings: Optional[Any] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StoreListResponse(BaseModel):
    id: int
    name: str
    code: str
    city: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    manager_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StoreStaffResponse(BaseModel):
    user_id: int
    username: str
    role_at_store: Optional[str] = None
    is_primary: bool
    joined_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StoreStaffAssign(BaseModel):
    user_id: int
    role_at_store: Optional[str] = None
    is_primary: bool = False
