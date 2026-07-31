from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.body_test import BodyTestRecord
from backend.schemas.ai import (
    BodyTestCreate,
    BodyTestResponse,
    BodyTestAnalysis,
    DashboardInsights,
)
from backend.schemas.common import ListResponse
from backend.services.ai import ai_service

router = APIRouter()


@router.post("/members/{member_id}/body-tests", response_model=BodyTestResponse, status_code=status.HTTP_201_CREATED)
async def create_body_test(
    member_id: int,
    obj_in: BodyTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = BodyTestRecord(**obj_in.model_dump(), member_id=member_id, organization_id=current_user.organization_id)
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


@router.get("/members/{member_id}/body-tests", response_model=ListResponse[BodyTestResponse])
async def get_body_tests(
    member_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select, func
    count_q = select(func.count(BodyTestRecord.id)).where(
        BodyTestRecord.member_id == member_id,
        BodyTestRecord.organization_id == current_user.organization_id,
    )
    total = (await db.execute(count_q)).scalar() or 0

    q = select(BodyTestRecord).where(
        BodyTestRecord.member_id == member_id,
        BodyTestRecord.organization_id == current_user.organization_id,
    ).order_by(BodyTestRecord.created_at.desc()).offset(skip).limit(limit)
    records = list((await db.execute(q)).scalars().all())

    return ListResponse(data=records, total=total, page=skip // limit + 1, page_size=limit)


@router.get("/members/{member_id}/body-tests/latest", response_model=BodyTestAnalysis)
async def analyze_body_test(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await ai_service.analyze_body_test(db, member_id, current_user.organization_id)
    return result


@router.get("/members/{member_id}/recommendations", response_model=list[dict])
async def recommend_courses(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recommendations = await ai_service.recommend_courses(db, member_id, current_user.organization_id)
    return recommendations


@router.get("/dashboard/insights", response_model=DashboardInsights)
async def get_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    insights = await ai_service.get_dashboard_insights(db, current_user.organization_id)
    return insights
