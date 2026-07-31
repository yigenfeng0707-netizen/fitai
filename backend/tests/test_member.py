import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_member(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/members/", json={
        "name": "张三",
        "phone": "13800138001",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "张三"
    assert data["phone"] == "13800138001"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_member_duplicate_phone(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/members/", json={
        "name": "张三", "phone": "13800138002",
    }, headers=auth_headers)
    response = await client.post("/api/v1/members/", json={
        "name": "李四", "phone": "13800138002",
    }, headers=auth_headers)
    assert response.status_code == 400
    assert "存在" in response.text


@pytest.mark.asyncio
async def test_get_member(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/members/", json={
        "name": "张三", "phone": "13800138003",
    }, headers=auth_headers)
    member_id = created.json()["id"]
    response = await client.get(f"/api/v1/members/{member_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "张三"


@pytest.mark.asyncio
async def test_get_member_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/members/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_member(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/members/", json={
        "name": "张三", "phone": "13800138004",
    }, headers=auth_headers)
    member_id = created.json()["id"]
    response = await client.put(f"/api/v1/members/{member_id}", json={
        "name": "张三丰",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "张三丰"


@pytest.mark.asyncio
async def test_delete_member(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/members/", json={
        "name": "张三", "phone": "13800138005",
    }, headers=auth_headers)
    member_id = created.json()["id"]
    response = await client.delete(f"/api/v1/members/{member_id}", headers=auth_headers)
    assert response.status_code == 200
    get_response = await client.get(f"/api/v1/members/{member_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_members_pagination(client: AsyncClient, auth_headers: dict):
    for i in range(5):
        await client.post("/api/v1/members/", json={
            "name": f"会员{i}", "phone": f"138001381{i:02d}",
        }, headers=auth_headers)
    response = await client.get("/api/v1/members/?skip=0&limit=3", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 3


@pytest.mark.asyncio
async def test_create_member_validation(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/members/", json={
        "name": "",
        "phone": "123",
    }, headers=auth_headers)
    assert response.status_code == 422
