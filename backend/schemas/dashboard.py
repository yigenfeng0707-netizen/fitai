"""
数据可视化仪表盘 Schema
"""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import date, datetime


class KPIItem(BaseModel):
    """KPI 指标项"""
    label: str
    value: Any  # float, int, or str
    unit: str = ""
    change: Optional[float] = None  # 变化百分比
    change_direction: Optional[str] = None  # "up", "down", "flat"
    icon: Optional[str] = None


class ChartDataPoint(BaseModel):
    """图表数据点"""
    label: str
    value: float
    secondary_value: Optional[float] = None  # 用于对比线


class ChartConfig(BaseModel):
    """图表配置"""
    chart_type: str  # line, bar, pie, gauge
    title: str
    data: list[ChartDataPoint]
    colors: list[str] = []


class StoreRankingItem(BaseModel):
    """门店排名项"""
    rank: int
    store_id: int
    store_name: str
    value: float
    change: float


class AlertItem(BaseModel):
    """预警信息项"""
    type: str  # warning, danger, info
    title: str
    message: str
    count: int = 1
    action_url: Optional[str] = None


class ExecutiveDashboardResponse(BaseModel):
    """高管仪表盘响应"""
    kpi: dict[str, KPIItem]
    revenue_chart: ChartConfig
    member_chart: ChartConfig
    booking_chart: ChartConfig
    store_ranking: list[StoreRankingItem]
    top_courses: list[dict]
    alerts: list[AlertItem]


class StoreDashboardResponse(BaseModel):
    """门店仪表盘响应"""
    kpi: dict[str, KPIItem]
    today_schedule: list[dict]
    revenue_chart: ChartConfig
    member_chart: ChartConfig
    coach_performance: list[dict]
    hourly_distribution: ChartConfig


class RealtimeResponse(BaseModel):
    """实时数据响应"""
    today_stats: dict
    ongoing_classes: list[dict]
    upcoming_classes: list[dict]
    staff_online: int
    alerts: list[AlertItem]


class YearOverYearResponse(BaseModel):
    """同比分析响应"""
    current_year: list[ChartDataPoint]
    previous_year: list[ChartDataPoint]
    months: list[str]
