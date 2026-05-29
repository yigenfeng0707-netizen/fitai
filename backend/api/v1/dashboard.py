"""API - 数据可视化仪表盘"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/executive")
async def get_executive_dashboard(
    period: str = Query("month", pattern="^(today|week|month|quarter|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """高管仪表盘 - 全组织概览"""
    data = await DashboardService.get_executive_dashboard(
        db, organization_id=current_user.organization_id, period=period,
    )
    return data


@router.get("/store/{store_id}")
async def get_store_dashboard(
    store_id: int,
    period: str = Query("month", pattern="^(today|week|month|quarter|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """门店仪表盘 - 单门店详情"""
    data = await DashboardService.get_store_dashboard(
        db, store_id=store_id, organization_id=current_user.organization_id, period=period,
    )
    return data


@router.get("/realtime")
async def get_realtime_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """实时数据"""
    data = await DashboardService.get_realtime_data(
        db, organization_id=current_user.organization_id,
    )
    return data


@router.get("/year-over-year")
async def get_year_over_year(
    metric: str = Query("revenue", pattern="^(revenue|members|bookings)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """同比分析"""
    data = await DashboardService.get_year_over_year_comparison(
        db, organization_id=current_user.organization_id, metric=metric,
    )
    return data


@router.get("/alerts")
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """仪表盘预警"""
    alerts = await DashboardService.get_dashboard_alerts(
        db, organization_id=current_user.organization_id,
    )
    return alerts
