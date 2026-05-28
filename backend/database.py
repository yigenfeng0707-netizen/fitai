"""
数据库连接
根据 APP_ENV 自动选择生产 (PostgreSQL) 或开发 (SQLite) 模式
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from backend.config import settings
from backend.database_base import Base


def _get_database_url() -> str:
    """根据环境获取数据库 URL"""
    is_test = os.getenv("APP_ENV") == "test"
    is_dev = settings.APP_ENV == "development"

    if is_test:
        return "sqlite+aiosqlite:///./test.db"

    if is_dev or settings.DATABASE_URL.startswith("sqlite"):
        sqlite_path = "./dev.db"
        return f"sqlite+aiosqlite:///{sqlite_path}"

    return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


def _get_sync_database_url() -> str:
    """获取同步数据库 URL (用于 Alembic 等)"""
    is_test = os.getenv("APP_ENV") == "test"
    is_dev = settings.APP_ENV == "development"

    if is_test:
        return "sqlite:///./test.db"

    if is_dev or "sqlite" in settings.DATABASE_URL:
        return "sqlite:///./dev.db"

    return settings.DATABASE_URL


def _is_sqlite(url: str) -> bool:
    return "sqlite" in url


_async_url = _get_database_url()

_sync_url = _get_sync_database_url()
_is_sqlite_db = _is_sqlite(_sync_url)

# 同步引擎 (用于 Alembic 迁移、脚本)
_sync_connect_args = {"check_same_thread": False} if _is_sqlite_db else {}
_sync_pool_kwargs = (
    {"poolclass": NullPool}
    if _is_sqlite_db
    else {
        "poolclass": QueuePool,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
    }
)
engine = create_engine(
    _sync_url,
    echo=settings.DEBUG,
    connect_args=_sync_connect_args,
    **_sync_pool_kwargs,
)

_is_async_sqlite = _is_sqlite(_async_url)

# 异步引擎 (用于 FastAPI)
_async_connect_args = {"check_same_thread": False} if _is_async_sqlite else {}
_async_pool_kwargs = (
    {
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
    if not _is_async_sqlite
    else {}
)
async_engine = create_async_engine(
    _async_url,
    echo=settings.DEBUG,
    connect_args=_async_connect_args,
    **_async_pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)


async def get_db():
    """获取数据库会话 (依赖注入)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    from sqlalchemy import select
    from backend.models import member, course, booking, coach, auth, order, organization, body_test, recommendation, lead, campaign  # noqa: F401
    from backend.models.organization import Organization
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Organization).limit(1))
            if not result.scalar_one_or_none():
                default_org = Organization(
                    name="默认机构",
                    slug="default",
                    plan="professional",
                )
                session.add(default_org)
                await session.commit()
                from backend.logger import logger
                logger.info("已创建默认机构 (id=1)")
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
