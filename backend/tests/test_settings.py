"""系统设置 API 测试"""
import pytest


class TestSettingsAPI:
    @pytest.mark.asyncio
    async def test_get_organization(self, client, auth_headers):
        resp = await client.get("/api/v1/settings/organization", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "slug" in data
        assert "plan" in data

    @pytest.mark.asyncio
    async def test_update_organization(self, client, auth_headers):
        resp = await client.put("/api/v1/settings/organization", json={
            "name": "测试门店",
            "contact_name": "张三",
            "contact_phone": "13800138000",
            "contact_email": "test@example.com",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "测试门店"
        assert data["contact_name"] == "张三"
        assert data["contact_phone"] == "13800138000"
        assert data["contact_email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_list_users(self, client, auth_headers):
        resp = await client.get("/api/v1/settings/users", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["data"]) >= 1

    @pytest.mark.asyncio
    async def test_create_user(self, client, db, auth_headers):
        resp = await client.post("/api/v1/settings/users", json={
            "username": "testreceptionist",
            "password": "test123456",
            "role": "receptionist",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testreceptionist"
        assert data["role"] == "receptionist"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, client, db, auth_headers):
        await client.post("/api/v1/settings/users", json={
            "username": "duplicateuser",
            "password": "test123456",
            "role": "coach",
        }, headers=auth_headers)
        resp = await client.post("/api/v1/settings/users", json={
            "username": "duplicateuser",
            "password": "test123456",
            "role": "coach",
        }, headers=auth_headers)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_update_user(self, client, db, auth_headers):
        resp = await client.post("/api/v1/settings/users", json={
            "username": "updatetest",
            "password": "test123456",
            "role": "receptionist",
        }, headers=auth_headers)
        user_id = resp.json()["id"]

        resp = await client.put(f"/api/v1/settings/users/{user_id}", json={
            "role": "coach",
            "is_active": False,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "coach"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_reset_password(self, client, db, auth_headers):
        resp = await client.post("/api/v1/settings/users", json={
            "username": "resetpwd",
            "password": "oldpassword",
            "role": "receptionist",
        }, headers=auth_headers)
        user_id = resp.json()["id"]

        resp = await client.put(f"/api/v1/settings/users/{user_id}", json={
            "password": "newpassword123",
        }, headers=auth_headers)
        assert resp.status_code == 200

        login_resp = await client.post("/api/v1/auth/login", json={
            "username": "resetpwd",
            "password": "newpassword123",
        })
        assert login_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_roles(self, client, auth_headers):
        resp = await client.get("/api/v1/settings/roles", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 4
        assert any(r["role"] == "super_admin" for r in data)
        assert any(r["role"] == "receptionist" for r in data)
