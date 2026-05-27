"""操作日志 API 测试"""
import pytest


class TestAuditLogAPI:
    @pytest.mark.asyncio
    async def test_empty_logs(self, client, auth_headers):
        resp = await client.get("/api/v1/audit-logs/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_create_member_creates_log(self, client, db, auth_headers):
        """创建会员时自动记录审计日志"""
        resp = await client.post("/api/v1/members/", json={
            "name": "审计会员",
            "phone": "13900020001",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        resp = await client.get("/api/v1/audit-logs/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        log = data["data"][0]
        assert log["action"] == "create"
        assert log["resource"] == "member"
        assert log["resource_id"] == member_id
        assert "审计会员" in log["detail"]

    @pytest.mark.asyncio
    async def test_pay_order_creates_log(self, client, db, auth_headers):
        """支付订单时自动记录审计日志"""
        resp = await client.post("/api/v1/members/", json={
            "name": "支付审计会员",
            "phone": "13900020002",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        resp = await client.post("/api/v1/orders/", json={
            "member_id": member_id,
            "amount": 500,
            "actual_amount": 450,
            "subject": "审计测试订单",
        }, headers=auth_headers)
        order_id = resp.json()["id"]

        resp = await client.post(f"/api/v1/orders/{order_id}/pay?payment_method=wechat", headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get("/api/v1/audit-logs/?action=pay", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["data"][0]["action"] == "pay"
        assert data["data"][0]["resource"] == "order"

    @pytest.mark.asyncio
    async def test_card_renew_creates_log(self, client, db, auth_headers):
        """续费时自动记录审计日志"""
        resp = await client.post("/api/v1/members/", json={
            "name": "续费审计会员",
            "phone": "13900020003",
            "initial_card_type": "monthly",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        resp = await client.post(f"/api/v1/cards/{member_id}/renew", json={
            "card_type": "yearly",
            "duration_days": 365,
            "amount": 3000,
        }, headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get("/api/v1/audit-logs/?action=card_renew", headers=auth_headers)
        data = resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_filter_by_resource(self, client, db, auth_headers):
        """按资源类型筛选"""
        resp = await client.post("/api/v1/members/", json={
            "name": "筛选会员",
            "phone": "13900020004",
        }, headers=auth_headers)

        resp = await client.get("/api/v1/audit-logs/?resource=member", headers=auth_headers)
        assert resp.status_code == 200
        assert all(log["resource"] == "member" for log in resp.json()["data"])

    @pytest.mark.asyncio
    async def test_manual_audit_log(self, client, db, auth_headers):
        """手动创建审计日志"""
        resp = await client.post("/api/v1/audit-logs/", json={
            "action": "custom_action",
            "resource": "test",
            "resource_id": 42,
            "detail": "自定义操作",
            "old_value": {"status": "pending"},
            "new_value": {"status": "done"},
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "custom_action"
        assert data["old_value"]["status"] == "pending"
        assert data["new_value"]["status"] == "done"
