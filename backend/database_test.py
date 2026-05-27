"""
数据库连接 - SQLite 测试模式
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.database_base import Base

# SQLite 内存数据库 (测试用) - 不使用连接池
engine = create_engine("sqlite:///./test.db", echo=False, connect_args={"check_same_thread": False})

async_engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=False)

AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
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
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from backend.logger import logger
    logger.info("测试数据库表创建完成")