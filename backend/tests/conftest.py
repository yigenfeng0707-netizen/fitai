import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.database_base import Base
from backend.database_test import async_engine as async_engine_test, AsyncSessionLocal as async_session_test
from backend.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with async_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 清理速率限制状态，避免测试间干扰
    from backend.core.rate_limiter import _requests
    _requests.clear()
    yield
    async with async_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_test() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_test() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def token(client: AsyncClient) -> str:
    from backend.models.organization import Organization
    from sqlalchemy import select
    async with async_session_test() as session:
        result = await session.execute(select(Organization).limit(1))
        if not result.scalar_one_or_none():
            session.add(Organization(name="测试门店", slug="test-org", plan="basic", status="active"))
            await session.commit()
    await client.post("/api/v1/auth/register", json={
        "username": "testadmin",
        "password": "Testpass123",
        "email": "testadmin@example.com",
        "role": "super_admin",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "testadmin",
        "password": "Testpass123",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
