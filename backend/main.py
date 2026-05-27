"""
健身/瑜伽/教培 AI 管理系统 - Phase 1 MVP
FastAPI 应用入口
"""
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.database import init_db
from backend.api.v1 import api_router
from backend.core.permissions import setup_permissions
from backend.logger import logger
from backend.exceptions import (
    AppException,
    NotFoundError,
    BusinessError,
    AuthenticationError,
    PermissionDeniedError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting %s v%s", settings.APP_NAME, "1.0.0")
    logger.info("Environment: %s", settings.APP_ENV)

    await init_db()
    setup_permissions()
    logger.info("Database initialized")
    logger.info("Permission system initialized")

    yield

    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="健身/瑜伽/教培 AI 管理系统 API",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS 配置
_cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=settings.APP_ENV != "production",
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 租户上下文中间件 ──

@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    request.state.organization_id = 1
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        try:
            from backend.core.security import verify_token
            payload = verify_token(token)
            if payload and "org_id" in payload:
                request.state.organization_id = payload["org_id"]
        except Exception:
            pass
    response = await call_next(request)
    return response


# ── 全局异常处理器 ──

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理自定义业务异常"""
    logger.warning("AppException: %s [%s]", exc.detail, exc.code)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.code,
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    """404 处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    """400 业务错误处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    """401 认证错误处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(PermissionDeniedError)
async def permission_error_handler(request: Request, exc: PermissionDeniedError):
    """403 权限错误处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局兜底异常处理"""
    request_id = str(uuid.uuid4())[:8]
    logger.exception("Unhandled exception [req=%s]: %s", request_id, str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "internal_error",
            "request_id": request_id,
        },
    )


# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
