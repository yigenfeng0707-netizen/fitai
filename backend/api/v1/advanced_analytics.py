"""API - 高级分析（核心指标报表）"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.schemas.analytics import (
    RevenueAnalysisResponse,
    MemberAnalysisResponse,
    CourseAnalysisResponse,
    ConversionFunnel,
)

router = APIRouter(prefix="/analytics/advanced", tags=["高级分析"])


@router.get("/revenue", response_model=RevenueAnalysisResponse)
async def get_revenue_analysis(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    store_id: Optional[int] = Query(None, description="门店ID"),
    group_by: str = Query("day", pattern="^(day|week|month)$", description="分组维度"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """营收分析 - 总营收、趋势、收入构成、环比增长"""
    from backend.services.advanced_analytics import AdvancedAnalyticsService
    data = await AdvancedAnalyticsService.get_revenue_analysis(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
        store_id=store_id,
    )
    return data


@router.get("/members", response_model=MemberAnalysisResponse)
async def get_member_analysis(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    store_id: Optional[int] = Query(None, description="门店ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """会员分析 - 新增/活跃/流失趋势、等级分布、卡类型分布"""
    from backend.services.advanced_analytics import AdvancedAnalyticsService
    data = await AdvancedAnalyticsService.get_member_analysis(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        store_id=store_id,
    )
    return data


@router.get("/courses", response_model=CourseAnalysisResponse)
async def get_course_analysis(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    store_id: Optional[int] = Query(None, description="门店ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """课程分析 - 热度排行、满课率、时段分布、类型占比"""
    from backend.services.advanced_analytics import AdvancedAnalyticsService
    data = await AdvancedAnalyticsService.get_course_analysis(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        store_id=store_id,
    )
    return data


@router.get("/coaches")
async def get_coach_performance(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    store_id: Optional[int] = Query(None, description="门店ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """教练绩效分析 - 课时排行、学员满意度、营收贡献、利用率"""
    from backend.services.advanced_analytics import AdvancedAnalyticsService
    data = await AdvancedAnalyticsService.get_coach_performance_analysis(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        store_id=store_id,
    )
    return data


@router.get("/funnel", response_model=ConversionFunnel)
async def get_conversion_funnel(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """转化漏斗 - 潜客→试课→购卡→复购→推荐的转化率"""
    from backend.services.advanced_analytics import AdvancedAnalyticsService
    data = await AdvancedAnalyticsService.get_conversion_funnel(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )
    return data


@router.get("/stores")
async def get_store_comparison(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """门店对比分析 - 各门店综合评分与各维度排名"""
    from backend.services.advanced_analytics import AdvancedAnalyticsService
    data = await AdvancedAnalyticsService.get_store_comparison_analytics(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )
    return data
