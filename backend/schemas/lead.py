from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend.models.lead import LeadSource, LeadStatus, LeadIntent


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    source: LeadSource = LeadSource.VISIT
    status: LeadStatus = LeadStatus.NEW
    intent: Optional[LeadIntent] = None
    expected_budget: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    assigned_to: Optional[int] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    intent: Optional[LeadIntent] = None
    expected_budget: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    assigned_to: Optional[int] = None
    converted_member_id: Optional[int] = None


class LeadResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    source: LeadSource = LeadSource.VISIT
    status: LeadStatus = LeadStatus.NEW
    intent: Optional[LeadIntent] = None
    expected_budget: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    follow_up_count: int = 0
    last_contacted_at: Optional[datetime] = None
    assigned_to: Optional[int] = None
    converted_member_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
