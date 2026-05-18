from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.settings import settings
from app.database import engine, Base
from app.api import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description="FitAI - 健身/瑜伽/教培 AI智能管理系统",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册权限中间件（仅在生产环境启用）
if settings.environment == "production":
    from app.auth.permission_middleware import GlobalPermissionMiddleware
    app.add_middleware(GlobalPermissionMiddleware)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "FitAI API Service", "version": settings.project_version}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "FitAI API",
        "version": settings.project_version,
        "environment": settings.ENVIRONMENT
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "error": str(exc) if settings.ENVIRONMENT == "development" else "请联系管理员"
        }
    )
