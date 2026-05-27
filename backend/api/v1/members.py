"""
API - 会员
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user, create_permission_checker
from backend.models.member import Member, MemberStatus, CardType
from backend.schemas.member import MemberCreate, MemberUpdate, MemberResponse
from backend.models.auth import User
from backend.schemas.common import BaseResponse, ListResponse

router = APIRouter()


@router.post("/", response_model=MemberResponse)
async def create_member(
    obj_in: MemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建会员"""
    from backend.crud.member import MemberCRUD
    # 检查手机号是否已存在
    existing = await MemberCRUD.get_by_phone(db, obj_in.phone)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已存在",
        )
    
    member = await MemberCRUD.create(db, obj_in, organization_id=current_user.organization_id)

    from backend.services.audit import AuditService
    await AuditService.log(db, action="create", resource="member", resource_id=member.id, detail=f"创建会员 {member.name}", user_id=current_user.id, organization_id=current_user.organization_id)

    return member


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会员详情"""
    from backend.crud.member import MemberCRUD
    member = await MemberCRUD.get(db, member_id)
    if not member or member.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会员不存在",
        )
    return member


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int,
    obj_in: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新会员"""
    from backend.crud.member import MemberCRUD
    member = await MemberCRUD.get(db, member_id)
    if not member or member.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会员不存在",
        )
    
    member = await MemberCRUD.update(db, member, obj_in)
    return member


@router.delete("/{member_id}", response_model=BaseResponse)
async def delete_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除会员"""
    from backend.crud.member import MemberCRUD
    member = await MemberCRUD.get(db, member_id)
    if not member or member.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会员不存在",
        )
    
    await MemberCRUD.delete(db, member)
    return BaseResponse(message="删除成功")


@router.get("/", response_model=ListResponse[MemberResponse])
async def get_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[MemberStatus] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会员列表"""
    from backend.crud.member import MemberCRUD
    members, total = await MemberCRUD.get_list(
        db, skip=skip, limit=limit, status=status, search=search,
        organization_id=current_user.organization_id,
    )
    
    return ListResponse(
        data=members,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.post("/{member_id}/consume", response_model=MemberResponse)
async def consume_session(
    member_id: int,
    amount: float = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """消费记录"""
    from backend.crud.member import MemberCRUD
    member = await MemberCRUD.get(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会员不存在",
        )
    
    if amount > 0:
        member = await MemberCRUD.add_consumption(db, member, amount)
    
    if member.card_type == CardType.SINGLE:
        member = await MemberCRUD.deduct_session(db, member)
    
    return member