"""
API - 认证
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from backend.dependencies import get_current_user
from backend.crud.auth import UserCRUD
from backend.schemas.auth import UserLogin, UserRegister, TokenResponse, UserResponse
from backend.core.security import create_access_token
from backend.database import get_db
from backend.models.auth import User

from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    obj_in: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    from sqlalchemy import select
    from backend.models.organization import Organization
    existing_user = await UserCRUD.get_by_username(db, obj_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    result = await db.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    org_id = org.id if org else 1

    user = await UserCRUD.create(
        db,
        username=obj_in.username,
        password=obj_in.password,
        role=obj_in.role.value,
        organization_id=org_id,
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    obj_in: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
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
    
    return TokenResponse(
        access_token=access_token,
        expires_in=60 * 60  # 1小时
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user