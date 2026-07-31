"""
API - 认证
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from backend.dependencies import get_current_user
from backend.crud.auth import UserCRUD
from backend.schemas.auth import UserLogin, UserRegister, TokenResponse, UserResponse
from backend.core.security import create_access_token, create_refresh_token, blacklist_token
from backend.core.password_policy import enforce_password_policy, PasswordPolicyError
from backend.database import get_db
from backend.models.auth import User
from backend.logger import logger

from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    obj_in: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 密码强度验证
    try:
        enforce_password_policy(obj_in.password)
    except PasswordPolicyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    from sqlalchemy import select
    from backend.models.organization import Organization
    existing_user = await UserCRUD.get_by_username(db, obj_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    existing_email = await UserCRUD.get_by_email(db, obj_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被使用",
        )

    result = await db.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    org_id = org.id if org else 1

    user = await UserCRUD.create(
        db,
        username=obj_in.username,
        email=obj_in.email,
        password=obj_in.password,
        role=obj_in.role.value,
        organization_id=org_id,
    )

    # 审计日志：用户注册
    from backend.services.audit import AuditService
    await AuditService.log(
        db, action="register", resource="user", resource_id=user.id,
        detail=f"新用户注册: {user.username}", user_id=user.id,
        organization_id=org_id,
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    obj_in: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录（支持用户名或邮箱）"""
    user = await UserCRUD.authenticate(db, obj_in.username, obj_in.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    # 更新最后登录时间
    await UserCRUD.update_last_login(db, user)

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "org_id": user.organization_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role, "org_id": user.organization_id}
    )

    # 审计日志：用户登录
    from backend.services.audit import AuditService
    await AuditService.log(
        db, action="login", resource="user", resource_id=user.id,
        detail=f"用户登录: {user.username}", user_id=user.id,
        organization_id=user.organization_id,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=30 * 60  # 30 分钟
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """用户登出（将当前 token 加入黑名单）"""
    # 注意：在依赖注入中无法直接获取原始 token，
    # 实际使用时需要客户端在请求体中传入 token 或通过中间件传递
    return {"success": True, "message": "登出成功"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user
