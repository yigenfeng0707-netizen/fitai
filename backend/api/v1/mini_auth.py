"""
API - 小程序认证
"""
import hashlib
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.core.security import create_access_token, get_password_hash
from backend.models.auth import User
from backend.schemas.auth import TokenResponse
from backend.schemas.mini import WxLoginRequest, PhoneLoginRequest

router = APIRouter(prefix="/mini", tags=["小程序"])


@router.post("/auth/wx-login", response_model=TokenResponse)
async def wx_login(
    obj_in: WxLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    微信小程序登录
    1. 用 code 换取 openid (stub - real impl needs wx API)
    2. 查找或创建用户
    3. 返回 JWT token
    """
    from sqlalchemy import select

    # Stub: 用 code 的哈希模拟 openid
    # 真实实现: 调用微信 API (https://api.weixin.qq.com/sns/jscode2session)
    # 用 code 换取 openid 和 session_key
    mock_openid = hashlib.sha256(obj_in.code.encode()).hexdigest()[:28]

    # 查找已有用户 (通过 username 存储 openid)
    result = await db.execute(
        select(User).where(User.username == f"wx_{mock_openid}")
    )
    user = result.scalar_one_or_none()

    if not user:
        # 首次登录，创建用户
        # 自动分配组织
        from sqlalchemy import select as sa_select
        from backend.models.organization import Organization
        org_result = await db.execute(sa_select(Organization).limit(1))
        org = org_result.scalar_one_or_none()
        if not org:
            # 系统无组织时自动创建默认组织
            org = Organization(name="默认组织", slug="default", plan="basic", status="active")
            db.add(org)
            await db.flush()
        user = User(
            username=f"wx_{mock_openid}",
            email=f"wx_{mock_openid}@mini.local",
            password_hash=get_password_hash(str(uuid.uuid4())),
            role="member",
            organization_id=org.id,
            is_active=True,
        )
        db.add(user)
        await db.flush()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    # 更新最后登录时间
    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None)
    await db.flush()

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "org_id": user.organization_id}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=60 * 60,  # 1小时
    )


@router.post("/auth/phone-login", response_model=TokenResponse)
async def phone_login(
    obj_in: PhoneLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    手机号登录（验证码）
    Stub: 接受任意验证码
    真实实现: 通过短信服务验证验证码
    """
    from sqlalchemy import select

    # Stub: 不验证验证码，直接通过
    # 真实实现: 调用短信服务验证 obj_in.verification_code

    # 通过手机号查找关联的会员
    from backend.models.member import Member
    result = await db.execute(
        select(Member).where(Member.phone == obj_in.phone)
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该手机号未注册会员",
        )

    # 查找关联的用户
    result = await db.execute(
        select(User).where(User.member_id == member.id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # 为会员创建关联用户
        user = User(
            username=f"phone_{obj_in.phone}",
            email=f"phone_{obj_in.phone}@mini.local",
            password_hash=get_password_hash(str(uuid.uuid4())),
            role="member",
            member_id=member.id,
            organization_id=member.organization_id,
            is_active=True,
        )
        db.add(user)
        await db.flush()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    # 更新最后登录时间
    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None)
    await db.flush()

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "org_id": user.organization_id}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=60 * 60,
    )
