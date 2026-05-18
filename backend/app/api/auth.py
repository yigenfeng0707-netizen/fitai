from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User, LoginLog
from app.schemas.auth import LoginRequest, LoginResponse, TokenRefreshRequest, TokenRefreshResponse
from app.auth.security import AuthService, LoginSecurity, get_client_ip, get_user_agent, RateLimiter

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录 - 包含完整安全检查
    """
    username = login_data.username
    password = login_data.password
    client_ip = get_client_ip(request)
    ua = get_user_agent(request)
    
    # 1. 限流检查
    rate_key = f"login:{client_ip}"
    allowed, remaining = RateLimiter.check_rate_limit(rate_key, max_requests=10, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试"
        )
    
    # 2. 登录失败次数检查
    is_locked, lockout_remaining = LoginSecurity.check_login_attempts(db, username)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"账号已被锁定，请{lockout_remaining}分钟后重试"
        )
    
    # 3. 查询用户
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        # 记录失败尝试
        LoginSecurity.record_login_attempt(
            db, username, client_ip, ua, success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 4. 验证密码
    if not AuthService.verify_password(password, user.hashed_password):
        # 记录失败尝试
        LoginSecurity.record_login_attempt(
            db, username, client_ip, ua, success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 5. 检查账号状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员"
        )
    
    # 6. 登录成功
    LoginSecurity.record_login_attempt(
        db, username, client_ip, ua, success=True
    )
    LoginSecurity.clear_login_attempts(db, username)
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 7. 生成Token
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role_id": user.role_id,
        "role_name": user.role_name,
        "tenant_id": user.tenant_id
    }
    
    access_token = AuthService.create_access_token(token_data)
    refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user_id=user.id,
        username=user.username,
        role_id=user.role_id,
        role_name=user.role_name
    )

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: Request,
    refresh_data: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    刷新Token
    """
    # 1. 验证refresh_token
    payload = AuthService.verify_token(refresh_data.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    # 2. 获取用户
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    # 3. 生成新的access_token
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role_id": user.role_id,
        "role_name": user.role_name,
        "tenant_id": user.tenant_id
    }
    
    access_token = AuthService.create_access_token(token_data)
    
    return TokenRefreshResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.post("/logout")
async def logout(request: Request):
    """
    退出登录
    """
    # 在生产环境中，应该将token加入黑名单
    return {"message": "退出成功"}

@router.post("/register")
async def register(
    request: Request,
    username: str,
    password: str,
    email: str = None,
    db: Session = Depends(get_db)
):
    """
    用户注册（仅演示环境可用）
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查密码强度
    is_strong, msg = AuthService.check_password_strength(password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"密码强度不足: {msg}"
        )
    
    # 创建用户
    hashed_password = AuthService.hash_password(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role_id=3,
        role_name="前台"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "注册成功",
        "user_id": new_user.id,
        "username": new_user.username
    }

@router.get("/me")
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role_id": current_user.role_id,
        "role_name": current_user.role_name,
        "last_login": current_user.last_login
    }

# 导入settings
from app.settings import settings
