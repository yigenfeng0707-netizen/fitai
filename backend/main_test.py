"""
FastAPI 应用入口 - 测试模式
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database_test import init_db  # 使用 SQLite 测试
from backend.api.v1 import api_router
from backend.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    logger.info("数据库初始化完成 (SQLite 测试模式)")

    yield

    logger.info("应用关闭中...")


app = FastAPI(
    title="健身瑜伽教培管理系统",
    description="Phase 1 MVP - SQLite 测试模式",
    version="0.1.0-test",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "0.1.0-test"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "健身瑜伽教培管理系统",
        "version": "0.1.0-test",
        "docs": "/docs",
        "health": "/health"
    }