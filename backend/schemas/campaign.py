from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from backend.models.campaign import CampaignStatus


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    campaign_type: str = "promotion"
    channels: Optional[list[str]] = None
    target_audience: Optional[dict] = None
    target_count: int = 0
    budget: float = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    channels: Optional[list[str]] = None
    target_audience: Optional[dict] = None
    target_count: Optional[int] = None
    budget: Optional[float] = None
    actual_cost: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sent_count: Optional[int] = None
    opened_count: Optional[int] = None
    converted_count: Optional[int] = None
    converted_revenue: Optional[float] = None


class CampaignResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    description: Optional[str] = None
    campaign_type: str
    status: CampaignStatus
    channels: Optional[list] = None
    target_audience: Optional[dict] = None
    target_count: int
    budget: float
    actual_cost: float
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sent_count: int
    opened_count: int
    converted_count: int
    converted_revenue: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
