"""
API - 教练
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.coach import Coach
from backend.schemas.coach import CoachCreate, CoachUpdate, CoachResponse
from backend.models.auth import User
from backend.schemas.common import BaseResponse, ListResponse

router = APIRouter()


@router.post("/", response_model=CoachResponse)
async def create_coach(
    obj_in: CoachCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建教练"""
    from backend.crud.coach import CoachCRUD
    # 检查手机号是否已存在
    existing = await CoachCRUD.get_by_phone(db, obj_in.phone)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已存在",
        )
    
    coach = await CoachCRUD.create(db, obj_in, organization_id=current_user.organization_id)
    return coach


@router.get("/{coach_id}", response_model=CoachResponse)
async def get_coach(
    coach_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取教练详情"""
    from backend.crud.coach import CoachCRUD
    coach = await CoachCRUD.get(db, coach_id)
    if not coach or coach.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教练不存在",
        )
    return coach


@router.put("/{coach_id}", response_model=CoachResponse)
async def update_coach(
    coach_id: int,
    obj_in: CoachUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新教练"""
    from backend.crud.coach import CoachCRUD
    coach = await CoachCRUD.get(db, coach_id)
    if not coach or coach.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教练不存在",
        )
    
    coach = await CoachCRUD.update(db, coach, obj_in)
    return coach


@router.delete("/{coach_id}", response_model=BaseResponse)
async def delete_coach(
    coach_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除教练"""
    from backend.crud.coach import CoachCRUD
    coach = await CoachCRUD.get(db, coach_id)
    if not coach or coach.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教练不存在",
        )
    
    await CoachCRUD.delete(db, coach)
    return BaseResponse(message="删除成功")


@router.get("/", response_model=ListResponse[CoachResponse])
async def get_coaches(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取教练列表"""
    from backend.crud.coach import CoachCRUD
    coaches, total = await CoachCRUD.get_list(
        db, skip=skip, limit=limit, is_active=is_active,
        organization_id=current_user.organization_id,
    )
    
    return ListResponse(
        data=coaches,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.post("/{coach_id}/add-hours", response_model=CoachResponse)
async def add_coach_hours(
    coach_id: int,
    hours: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """增加教练课时"""
    from backend.crud.coach import CoachCRUD
    coach = await CoachCRUD.get(db, coach_id)
    if not coach or coach.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教练不存在",
        )
    
    if hours <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="课时必须大于0",
        )
    
    coach = await CoachCRUD.add_hours(db, coach, hours)
    return coach