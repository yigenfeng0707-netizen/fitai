from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BodyTestCreate(BaseModel):
    height: Optional[float] = None
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass: Optional[float] = None
    bmi: Optional[float] = None
    bone_mass: Optional[float] = None
    body_water: Optional[float] = None
    visceral_fat: Optional[float] = None
    basal_metabolism: Optional[float] = None
    body_age: Optional[int] = None
    protein: Optional[float] = None
    score: Optional[float] = None
    extra_data: Optional[dict] = None
    notes: Optional[str] = None


class BodyTestResponse(BaseModel):
    id: int
    member_id: int
    organization_id: int
    height: Optional[float] = None
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass: Optional[float] = None
    bmi: Optional[float] = None
    bone_mass: Optional[float] = None
    body_water: Optional[float] = None
    visceral_fat: Optional[float] = None
    basal_metabolism: Optional[float] = None
    body_age: Optional[int] = None
    protein: Optional[float] = None
    score: Optional[float] = None
    extra_data: Optional[dict] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BodyTestAnalysis(BaseModel):
    current: Optional[BodyTestResponse] = None
    previous: Optional[BodyTestResponse] = None
    trends: dict = {}
    suggestions: list[str] = []


class RecommendationResponse(BaseModel):
    id: int
    recommendation_type: str
    member_id: Optional[int] = None
    title: str
    content: Optional[str] = None
    score: Optional[float] = None
    reason: Optional[str] = None
    action_url: Optional[str] = None
    is_read: bool = False
    is_applied: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InsightItem(BaseModel):
    label: str
    value: str
    change: Optional[str] = None
    trend: Optional[str] = None


class DashboardInsights(BaseModel):
    revenue_today: float = 0
    revenue_month: float = 0
    active_members: int = 0
    new_members_month: int = 0
    bookings_today: int = 0
    class_completion_rate: float = 0
    top_courses: list[dict] = []
    insights: list[str] = []
