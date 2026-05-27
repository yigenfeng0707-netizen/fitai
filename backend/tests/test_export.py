"""数据导出 API 测试"""
import pytest


class TestExportAPI:
    @pytest.mark.asyncio
    async def test_export_members(self, client, auth_headers):
        resp = await client.get("/api/v1/export/members", headers=auth_headers)
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers.get("content-type", "")
        assert len(resp.content) > 0

    @pytest.mark.asyncio
    async def test_export_orders(self, client, auth_headers):
        resp = await client.get("/api/v1/export/orders", headers=auth_headers)
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_export_bookings(self, client, auth_headers):
        resp = await client.get("/api/v1/export/bookings", headers=auth_headers)
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_export_leads(self, client, auth_headers):
        resp = await client.get("/api/v1/export/leads", headers=auth_headers)
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_export_invalid_resource(self, client, auth_headers):
        resp = await client.get("/api/v1/export/invalid", headers=auth_headers)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_export_with_data(self, client, db, auth_headers):
        """有数据时导出正常"""
        await client.post("/api/v1/members/", json={
            "name": "导出会员",
            "phone": "13900030001",
        }, headers=auth_headers)

        resp = await client.get("/api/v1/export/members", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.headers.get("content-disposition") is not None
        assert len(resp.content) > 500
