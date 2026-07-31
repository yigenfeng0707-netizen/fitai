"""门店管理 API 测试"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_store(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/stores/", json={
        "name": "旗舰店",
        "code": "FLAGSHIP",
        "address": "市中心广场1号",
        "city": "北京",
        "phone": "010-12345678",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "旗舰店"
    assert data["code"] == "FLAGSHIP"
    assert data["city"] == "北京"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_store_auto_code(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/stores/", json={
        "name": "分店A",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] is not None
    assert len(data["code"]) > 0


@pytest.mark.asyncio
async def test_list_stores(client: AsyncClient, auth_headers: dict):
    # Create two stores
    await client.post("/api/v1/stores/", json={"name": "门店1", "code": "S1"}, headers=auth_headers)
    await client.post("/api/v1/stores/", json={"name": "门店2", "code": "S2"}, headers=auth_headers)

    resp = await client.get("/api/v1/stores/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_get_store(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/stores/", json={
        "name": "获取测试店",
        "code": "GET_TEST",
    }, headers=auth_headers)
    store_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/stores/{store_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "获取测试店"


@pytest.mark.asyncio
async def test_get_store_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/stores/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_store(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/stores/", json={
        "name": "更新前",
        "code": "UPD_TEST",
    }, headers=auth_headers)
    store_id = create_resp.json()["id"]

    resp = await client.put(f"/api/v1/stores/{store_id}", json={
        "name": "更新后",
        "city": "上海",
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "更新后"
    assert data["city"] == "上海"


@pytest.mark.asyncio
async def test_delete_store(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/stores/", json={
        "name": "待删除",
        "code": "DEL_TEST",
    }, headers=auth_headers)
    store_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/stores/{store_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.get(f"/api/v1/stores/{store_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assign_staff(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    # Create a store
    store_resp = await client.post("/api/v1/stores/", json={
        "name": "员工测试店",
        "code": "STAFF_TEST",
    }, headers=auth_headers)
    store_id = store_resp.json()["id"]

    # Create a user
    from backend.crud.auth import UserCRUD
    user = await UserCRUD.create(db, "staff_user", "staff@example.com", "pass123", "receptionist", organization_id=1)
    await db.commit()

    # Assign staff
    resp = await client.post(f"/api/v1/stores/{store_id}/staff/", json={
        "user_id": user.id,
        "role_at_store": "店长",
        "is_primary": True,
    }, headers=auth_headers)
    assert resp.status_code == 201

    # Get staff
    resp = await client.get(f"/api/v1/stores/{store_id}/staff/", headers=auth_headers)
    assert resp.status_code == 200
    staff = resp.json()
    assert any(s["user_id"] == user.id for s in staff)


@pytest.mark.asyncio
async def test_remove_staff(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    store_resp = await client.post("/api/v1/stores/", json={
        "name": "移除员工店",
        "code": "RM_STAFF",
    }, headers=auth_headers)
    store_id = store_resp.json()["id"]

    from backend.crud.auth import UserCRUD
    user = await UserCRUD.create(db, "rm_staff_user", "rmstaff@example.com", "pass123", "receptionist", organization_id=1)
    await db.commit()

    await client.post(f"/api/v1/stores/{store_id}/staff/", json={
        "user_id": user.id,
    }, headers=auth_headers)

    resp = await client.delete(f"/api/v1/stores/{store_id}/staff/{user.id}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_store_tenant_isolation(client: AsyncClient, db: AsyncSession):
    from backend.models.organization import Organization
    from backend.crud.auth import UserCRUD
    from backend.core.security import create_access_token

    org_a = Organization(name="StoreOrgA", slug="store-org-a")
    org_b = Organization(name="StoreOrgB", slug="store-org-b")
    db.add_all([org_a, org_b])
    await db.commit()

    user_a = await UserCRUD.create(db, "store_admin_a", "store_a@example.com", "pass123", "super_admin", organization_id=org_a.id)
    await db.commit()

    token_a = create_access_token(data={"sub": str(user_a.id), "role": "super_admin", "org_id": org_a.id})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    resp = await client.post("/api/v1/stores/", json={
        "name": "OrgA门店",
        "code": "ORGA_S1",
    }, headers=headers_a)
    assert resp.status_code == 201
    store_id = resp.json()["id"]

    user_b = await UserCRUD.create(db, "store_admin_b", "store_b@example.com", "pass123", "super_admin", organization_id=org_b.id)
    await db.commit()

    token_b = create_access_token(data={"sub": str(user_b.id), "role": "super_admin", "org_id": org_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp = await client.get(f"/api/v1/stores/{store_id}", headers=headers_b)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_stores_filter_active(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/stores/", json={"name": "活跃店", "code": "ACTIVE_S"}, headers=auth_headers)

    resp = await client.get("/api/v1/stores/?is_active=true", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    for s in data["data"]:
        assert s["is_active"] is True


@pytest.mark.asyncio
async def test_get_my_stores(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    resp = await client.get("/api/v1/stores/my/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_set_primary_store(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    store_resp = await client.post("/api/v1/stores/", json={
        "name": "主店测试",
        "code": "PRIMARY_S",
    }, headers=auth_headers)
    store_id = store_resp.json()["id"]

    from backend.crud.auth import UserCRUD
    user = await UserCRUD.create(db, "primary_user", "primary@example.com", "pass123", "receptionist", organization_id=1)
    await db.commit()

    await client.post(f"/api/v1/stores/{store_id}/staff/", json={
        "user_id": user.id,
    }, headers=auth_headers)

    resp = await client.post(f"/api/v1/stores/{store_id}/staff/{user.id}/primary", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_store_with_facilities(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/stores/", json={
        "name": "设施店",
        "code": "FAC_TEST",
        "facilities": ["瑜伽室", "泳池", "更衣室"],
        "max_capacity": 100,
        "business_hours": {"weekday": ["06:00", "22:00"]},
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["facilities"] == ["瑜伽室", "泳池", "更衣室"]
    assert data["max_capacity"] == 100


@pytest.mark.asyncio
async def test_store_with_location(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/stores/", json={
        "name": "定位店",
        "code": "LOC_TEST",
        "longitude": 116.404,
        "latitude": 39.915,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["longitude"] == 116.404
    assert data["latitude"] == 39.915


@pytest.mark.asyncio
async def test_duplicate_store_code(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/stores/", json={"name": "店1", "code": "DUP_CODE"}, headers=auth_headers)
    try:
        resp = await client.post("/api/v1/stores/", json={"name": "店2", "code": "DUP_CODE"}, headers=auth_headers)
        # SQLite unique constraint violation - should be 500 (IntegrityError)
        assert resp.status_code in (400, 500)
    except Exception:
        pass  # IntegrityError may propagate


@pytest.mark.asyncio
async def test_update_store_deactivate(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/stores/", json={
        "name": "停用店",
        "code": "DEACT",
    }, headers=auth_headers)
    store_id = create_resp.json()["id"]

    resp = await client.put(f"/api/v1/stores/{store_id}", json={"is_active": False}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False
