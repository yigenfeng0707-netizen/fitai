import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Pass123456",
        "role": "receptionist",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "receptionist"


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "dupuser", "email": "dupuser@example.com", "password": "Pass123456",
    })
    response = await client.post("/api/v1/auth/register", json={
        "username": "dupuser", "email": "dupuser2@example.com", "password": "Pass123456",
    })
    assert response.status_code == 400
    assert "已存在" in response.text


@pytest.mark.asyncio
async def test_login_form(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "loginuser", "email": "loginuser@example.com", "password": "Pass123456",
    })
    response = await client.post("/api/v1/auth/login", json={
        "username": "loginuser",
        "password": "Pass123456",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "username": "nonexistent",
        "password": "Wrongpass123",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert "role" in data
