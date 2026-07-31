"""API - 经营分析"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取经营分析仪表盘数据"""
    from backend.services.analytics import AnalyticsService
    data = await AnalyticsService.get_dashboard_data(
        db, organization_id=current_user.organization_id,
    )
    return data
