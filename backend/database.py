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
    from backend.models import member, course, booking, coach, auth, order, organization, body_test, recommendation, lead, campaign, automation  # noqa: F401
    from backend.models.organization import Organization
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Organization).limit(1))
            org = result.scalar_one_or_none()
            if not org:
                org = Organization(
                    name="默认机构",
                    slug="default",
                    plan="professional",
                )
                session.add(org)
                await session.flush()

            # 检查是否需要种子数据
            from backend.models.member import Member, MemberStatus, CardType
            from backend.models.coach import Coach
            from backend.models.course import Course, CourseType, CourseSchedule
            from datetime import datetime, timedelta

            existing_members = await session.execute(select(Member).limit(1))
            if not existing_members.scalar_one_or_none():
                # 种子教练
                coaches = [
                    Coach(name="张教练", phone="13800000001", specialization="瑜伽", is_active=True, organization_id=org.id),
                    Coach(name="李教练", phone="13800000002", specialization="普拉提", is_active=True, organization_id=org.id),
                    Coach(name="王教练", phone="13800000003", specialization="健身", is_active=True, organization_id=org.id),
                ]
                for c in coaches:
                    session.add(c)
                await session.flush()

                # 种子会员
                members = [
                    Member(name="赵一", phone="13900000001", gender="女", card_type=CardType.YEARLY,
                           card_start_date=datetime(2026, 1, 1), card_end_date=datetime(2026, 12, 31),
                           level=3, total_consumption=12800, status=MemberStatus.ACTIVE, organization_id=org.id),
                    Member(name="钱二", phone="13900000002", gender="女", card_type=CardType.MONTHLY,
                           card_start_date=datetime(2026, 5, 1), card_end_date=datetime(2026, 6, 1),
                           level=2, total_consumption=3200, status=MemberStatus.ACTIVE, organization_id=org.id),
                    Member(name="孙三", phone="13900000003", gender="男", card_type=CardType.SINGLE,
                           card_remaining_count=10, level=1, total_consumption=1500,
                           status=MemberStatus.ACTIVE, organization_id=org.id),
                    Member(name="周四", phone="13900000004", gender="女", card_type=CardType.STORED,
                           card_balance=5000, level=4, total_consumption=25000,
                           status=MemberStatus.ACTIVE, organization_id=org.id),
                    Member(name="吴五", phone="13900000005", gender="男", card_type=CardType.QUARTERLY,
                           card_start_date=datetime(2026, 3, 1), card_end_date=datetime(2026, 6, 1),
                           level=2, total_consumption=4800, status=MemberStatus.ACTIVE, organization_id=org.id),
                ]
                for m in members:
                    session.add(m)
                await session.flush()

                # 种子课程
                courses = [
                    Course(name="哈他瑜伽基础", course_type=CourseType.GROUP, duration_minutes=60,
                           price=80, room="瑜伽1室", max_attendees=15, is_active=True, organization_id=org.id),
                    Course(name="流瑜伽", course_type=CourseType.GROUP, duration_minutes=75,
                           price=100, room="瑜伽1室", max_attendees=12, is_active=True, organization_id=org.id),
                    Course(name="普拉提核心训练", course_type=CourseType.PRIVATE, duration_minutes=60,
                           price=300, room="私教室A", max_attendees=1, is_active=True, organization_id=org.id),
                    Course(name="力量训练", course_type=CourseType.PRIVATE, duration_minutes=60,
                           price=350, room="私教室B", max_attendees=1, is_active=True, organization_id=org.id),
                    Course(name="阴瑜伽放松", course_type=CourseType.GROUP, duration_minutes=90,
                           price=120, room="瑜伽2室", max_attendees=20, is_active=True, organization_id=org.id),
                ]
                for c in courses:
                    session.add(c)
                await session.flush()

                # 种子排期（今日到未来7天）
                now = datetime.utcnow()
                for day_offset in range(7):
                    day = now + timedelta(days=day_offset)
                    for hour in [9, 10, 14, 16, 18]:
                        schedule = CourseSchedule(
                            course_id=courses[day_offset % len(courses)].id,
                            start_time=day.replace(hour=hour, minute=0, second=0, microsecond=0),
                            end_time=day.replace(hour=hour + 1, minute=0, second=0, microsecond=0),
                            status="scheduled",
                            enrolled_count=0,
                            organization_id=org.id,
                        )
                        session.add(schedule)

                await session.commit()
                from backend.logger import logger
                logger.info("种子数据已初始化")
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
