"""高级分析 - 数据模型"""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import date, datetime


class RevenueOverview(BaseModel):
    """营收概览"""
    total_revenue: float = 0.0
    order_count: int = 0
    avg_order_value: float = 0.0
    refund_amount: float = 0.0
    net_revenue: float = 0.0
    growth_rate: float = 0.0  # vs previous period


class RevenueTrendItem(BaseModel):
    """营收趋势项"""
    period: str  # date string
    revenue: float = 0.0
    order_count: int = 0
    avg_order_value: float = 0.0


class RevenueComposition(BaseModel):
    """收入构成"""
    new_purchase: float = 0.0
    renewal: float = 0.0
    upgrade: float = 0.0
    other: float = 0.0


class RevenueAnalysisResponse(BaseModel):
    """营收分析响应"""
    overview: RevenueOverview
    trend: list[RevenueTrendItem]
    composition: RevenueComposition
    top_products: list[dict]


class MemberOverview(BaseModel):
    """会员概览"""
    total_members: int = 0
    new_members: int = 0
    active_members: int = 0
    churned_members: int = 0
    net_growth: int = 0
    growth_rate: float = 0.0


class MemberDistribution(BaseModel):
    """会员分布"""
    by_level: dict = {}
    by_card_type: dict = {}
    by_source: dict = {}
    by_store: list[dict] = []


class MemberAnalysisResponse(BaseModel):
    """会员分析响应"""
    overview: MemberOverview
    trend: list[dict]
    distribution: MemberDistribution
    avg_consumption: float = 0.0


class CourseAnalysisResponse(BaseModel):
    """课程分析响应"""
    top_courses: list[dict] = []  # [{name, booking_count, fill_rate, revenue}]
    type_distribution: dict = {}  # {type: count}
    time_slot_distribution: list[dict] = []  # [{hour, count}]
    avg_fill_rate: float = 0.0


class CoachPerformanceItem(BaseModel):
    """教练绩效项"""
    coach_id: int = 0
    coach_name: str = ""
    store_name: Optional[str] = None
    classes_taught: int = 0
    total_students: int = 0
    avg_rating: float = 0.0
    revenue_contribution: float = 0.0
    utilization_rate: float = 0.0


class ConversionFunnel(BaseModel):
    """转化漏斗"""
    leads: int = 0
    trials: int = 0
    conversions: int = 0
    renewals: int = 0
    referrals: int = 0
    lead_to_trial_rate: float = 0.0
    trial_to_conversion_rate: float = 0.0
    conversion_to_renewal_rate: float = 0.0


class StoreComparisonItem(BaseModel):
    """门店对比项"""
    store_id: int = 0
    store_name: str = ""
    total_revenue: float = 0.0
    total_members: int = 0
    total_bookings: int = 0
    avg_fill_rate: float = 0.0
    new_members: int = 0
    score: float = 0.0


class AnalyticsQueryParams(BaseModel):
    """分析查询参数"""
    start_date: date
    end_date: date
    store_id: Optional[int] = None
    group_by: str = "day"
