"""
API - 系统设置
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.organization import Organization
from backend.schemas.settings import (
    OrganizationUpdate, OrganizationResponse,
    UserCreateByAdmin, UserUpdateByAdmin, UserManageResponse,
)
from backend.schemas.common import ListResponse

router = APIRouter()


@router.get("/organization", response_model=OrganizationResponse)
async def get_organization(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    return org


@router.put("/organization", response_model=OrganizationResponse)
async def update_organization(
    obj_in: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)
    await db.flush()
    return org


@router.get("/users", response_model=ListResponse[UserManageResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(User).where(User.organization_id == current_user.organization_id)
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    result = await db.execute(query.offset(skip).limit(limit).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return ListResponse(data=users, total=total, page=skip // limit + 1, page_size=limit)


@router.post("/users", response_model=UserManageResponse)
async def create_user(
    obj_in: UserCreateByAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.auth import UserCRUD
    existing = await UserCRUD.get_by_username(db, obj_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = await UserCRUD.create(
        db, username=obj_in.username, email=obj_in.email, password=obj_in.password,
        role=obj_in.role, organization_id=current_user.organization_id,
    )
    return user


@router.put("/users/{user_id}", response_model=UserManageResponse)
async def update_user(
    user_id: int,
    obj_in: UserUpdateByAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.auth import UserCRUD
    from backend.core.security import get_password_hash
    from backend.core.password_policy import enforce_password_policy, PasswordPolicyError
    from backend.services.audit import AuditService
    user = await UserCRUD.get(db, user_id)
    if not user or user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="用户不存在")

    changes = []
    if obj_in.role is not None:
        changes.append(f"角色: {user.role} -> {obj_in.role}")
        user.role = obj_in.role
    if obj_in.is_active is not None:
        changes.append(f"状态: {user.is_active} -> {obj_in.is_active}")
        user.is_active = obj_in.is_active
    if obj_in.password:
        # 密码强度验证
        try:
            enforce_password_policy(obj_in.password)
        except PasswordPolicyError as e:
            raise HTTPException(status_code=400, detail=str(e))
        user.password_hash = get_password_hash(obj_in.password)
        changes.append("密码已修改")

    await db.flush()

    # 审计日志：用户信息变更（密码、权限等敏感操作）
    if changes:
        await AuditService.log(
            db, action="update", resource="user", resource_id=user.id,
            detail=f"管理员修改用户: {', '.join(changes)}",
            user_id=current_user.id,
            organization_id=current_user.organization_id,
        )

    return user


@router.get("/roles")
async def list_roles():
    from backend.core.permissions import ROLE_PERMISSIONS
    return [
        {"role": role.value, "permissions": sorted(list(perms))}
        for role, perms in ROLE_PERMISSIONS.items()
    ]
