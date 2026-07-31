import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_coach(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/coaches/", json={
        "name": "王教练",
        "phone": "13900139001",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "王教练"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_coach(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/coaches/", json={
        "name": "王教练", "phone": "13900139002",
    }, headers=auth_headers)
    coach_id = created.json()["id"]
    response = await client.get(f"/api/v1/coaches/{coach_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "王教练"


@pytest.mark.asyncio
async def test_update_coach(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/coaches/", json={
        "name": "王教练", "phone": "13900139003",
    }, headers=auth_headers)
    coach_id = created.json()["id"]
    response = await client.put(f"/api/v1/coaches/{coach_id}", json={
        "is_active": False,
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_coach(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/coaches/", json={
        "name": "王教练", "phone": "13900139004",
    }, headers=auth_headers)
    coach_id = created.json()["id"]
    response = await client.delete(f"/api/v1/coaches/{coach_id}", headers=auth_headers)
    assert response.status_code == 200
    get_response = await client.get(f"/api/v1/coaches/{coach_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_coach_duplicate_phone(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/coaches/", json={
        "name": "王教练", "phone": "13900139005",
    }, headers=auth_headers)
    response = await client.post("/api/v1/coaches/", json={
        "name": "李教练", "phone": "13900139005",
    }, headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_coach_add_hours(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/coaches/", json={
        "name": "王教练", "phone": "13900139006",
    }, headers=auth_headers)
    coach_id = created.json()["id"]
    response = await client.post(f"/api/v1/coaches/{coach_id}/add-hours?hours=5", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total_hours"] == 5


@pytest.mark.asyncio
async def test_coach_add_hours_negative(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/coaches/", json={
        "name": "王教练", "phone": "13900139007",
    }, headers=auth_headers)
    coach_id = created.json()["id"]
    response = await client.post(f"/api/v1/coaches/{coach_id}/add-hours?hours=-1", headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_coaches(client: AsyncClient, auth_headers: dict):
    for i in range(3):
        await client.post("/api/v1/coaches/", json={
            "name": f"教练{i}", "phone": f"139001391{i:02d}",
        }, headers=auth_headers)
    response = await client.get("/api/v1/coaches/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["total"] == 3
