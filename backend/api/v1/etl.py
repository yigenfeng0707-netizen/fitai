"""API - 数据仓库 / ETL"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.daily_stats import DailyStats
from backend.models.member_lifecycle import MemberLifecycleEvent
from backend.models.coach_stats import CoachDailyStats
from backend.services.etl_service import ETLService

router = APIRouter(prefix="/warehouse", tags=["数据仓库"])


@router.post("/etl/daily")
async def trigger_daily_etl(
    stat_date: date = Query(..., description="统计日期"),
    store_id: Optional[int] = Query(None, description="门店ID，不传则生成全组织统计"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发每日数据ETL"""
    result = await ETLService.generate_daily_stats(
        db, organization_id=current_user.organization_id,
        stat_date=stat_date, store_id=store_id,
    )
    return result


@router.post("/etl/lifecycle")
async def trigger_lifecycle_etl(
    event_date: date = Query(..., description="事件日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发会员生命周期事件检测"""
    result = await ETLService.generate_member_lifecycle_events(
        db, organization_id=current_user.organization_id,
        event_date=event_date,
    )
    return result


@router.post("/etl/coach-stats")
async def trigger_coach_stats_etl(
    stat_date: date = Query(..., description="统计日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发教练统计ETL"""
    result = await ETLService.generate_coach_daily_stats(
        db, organization_id=current_user.organization_id,
        stat_date=stat_date,
    )
    return result


@router.post("/etl/backfill")
async def backfill(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """回填历史数据"""
    from backend.services.audit import AuditService
    await AuditService.log(
        db, action="data_export", resource="warehouse", resource_id=None,
        detail=f"数据回填: {start_date} ~ {end_date}",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    result = await ETLService.backfill_stats(
        db, organization_id=current_user.organization_id,
        start_date=start_date, end_date=end_date,
    )
    return result


@router.get("/stats")
async def get_daily_stats(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    store_id: Optional[int] = Query(None, description="门店ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询每日统计数据"""
    conditions = [
        DailyStats.organization_id == current_user.organization_id,
        DailyStats.stat_date >= start_date,
        DailyStats.stat_date <= end_date,
    ]
    if store_id is not None:
        conditions.append(DailyStats.store_id == store_id)

    result = await db.execute(
        select(DailyStats)
        .where(*conditions)
        .order_by(DailyStats.stat_date)
    )
    stats = result.scalars().all()

    return [
        {
            "id": s.id,
            "stat_date": s.stat_date.isoformat(),
            "store_id": s.store_id,
            "total_revenue": s.total_revenue,
            "order_count": s.order_count,
            "new_members_revenue": s.new_members_revenue,
            "renewal_revenue": s.renewal_revenue,
            "refund_amount": s.refund_amount,
            "avg_order_value": s.avg_order_value,
            "total_members": s.total_members,
            "new_members": s.new_members,
            "active_members": s.active_members,
            "expired_members": s.expired_members,
            "frozen_members": s.frozen_members,
            "total_bookings": s.total_bookings,
            "checked_in": s.checked_in,
            "cancelled_bookings": s.cancelled_bookings,
            "no_shows": s.no_shows,
            "checkin_rate": s.checkin_rate,
            "total_classes": s.total_classes,
            "avg_fill_rate": s.avg_fill_rate,
            "popular_course_id": s.popular_course_id,
            "popular_course_name": s.popular_course_name,
            "active_coaches": s.active_coaches,
            "total_teaching_hours": s.total_teaching_hours,
        }
        for s in stats
    ]


@router.get("/member-lifecycle")
async def get_member_lifecycle(
    member_id: Optional[int] = Query(None, description="会员ID"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询会员生命周期事件"""
    conditions = [
        MemberLifecycleEvent.organization_id == current_user.organization_id,
    ]
    if member_id is not None:
        conditions.append(MemberLifecycleEvent.member_id == member_id)
    if event_type is not None:
        conditions.append(MemberLifecycleEvent.event_type == event_type)
    if start_date is not None:
        conditions.append(MemberLifecycleEvent.event_date >= start_date)
    if end_date is not None:
        conditions.append(MemberLifecycleEvent.event_date <= end_date)

    result = await db.execute(
        select(MemberLifecycleEvent)
        .where(*conditions)
        .order_by(MemberLifecycleEvent.event_date.desc(), MemberLifecycleEvent.id.desc())
        .limit(500)
    )
    events = result.scalars().all()

    return [
        {
            "id": e.id,
            "member_id": e.member_id,
            "store_id": e.store_id,
            "event_type": e.event_type,
            "event_date": e.event_date.isoformat(),
            "event_data": e.event_data,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/coach-stats")
async def get_coach_stats(
    coach_id: Optional[int] = Query(None, description="教练ID"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询教练统计数据"""
    conditions = [
        CoachDailyStats.organization_id == current_user.organization_id,
        CoachDailyStats.stat_date >= start_date,
        CoachDailyStats.stat_date <= end_date,
    ]
    if coach_id is not None:
        conditions.append(CoachDailyStats.coach_id == coach_id)

    result = await db.execute(
        select(CoachDailyStats)
        .where(*conditions)
        .order_by(CoachDailyStats.stat_date, CoachDailyStats.coach_id)
    )
    stats = result.scalars().all()

    return [
        {
            "id": s.id,
            "coach_id": s.coach_id,
            "store_id": s.store_id,
            "stat_date": s.stat_date.isoformat(),
            "classes_taught": s.classes_taught,
            "total_students": s.total_students,
            "avg_rating": s.avg_rating,
            "total_hours": s.total_hours,
            "new_students": s.new_students,
            "revenue_contribution": s.revenue_contribution,
        }
        for s in stats
    ]


@router.get("/retention/cohorts")
async def get_retention_cohorts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """会员留存分析"""
    result = await ETLService.get_member_retention_cohorts(
        db, organization_id=current_user.organization_id,
    )
    return result


@router.get("/retention/lifetime-value")
async def get_lifetime_value(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """会员生命周期价值"""
    result = await ETLService.get_member_lifetime_value(
        db, organization_id=current_user.organization_id,
    )
    return result


@router.get("/retention/churn")
async def get_churn_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """流失分析"""
    result = await ETLService.get_churn_analysis(
        db, organization_id=current_user.organization_id,
    )
    return result
