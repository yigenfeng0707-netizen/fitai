"""会员卡管理 API 测试"""
import pytest
from datetime import datetime, timedelta


class TestCardManagement:
    @pytest.mark.asyncio
    async def test_renew_card(self, client, db, auth_headers):
        """续费操作"""
        resp = await client.post("/api/v1/members/", json={
            "name": "续费会员",
            "phone": "13900008888",
            "initial_card_type": "monthly",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        resp = await client.post(f"/api/v1/cards/{member_id}/renew", json={
            "card_type": "yearly",
            "duration_days": 365,
            "amount": 3000,
            "description": "年卡续费",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_type"] == "renew"
        assert data["amount"] == 3000
        assert data["card_type_after"] == "yearly"
        assert data["description"] == "年卡续费"

        member_resp = await client.get(f"/api/v1/members/{member_id}", headers=auth_headers)
        member = member_resp.json()
        assert member["card_type"] == "yearly"
        assert member["card_end_date"] is not None

    @pytest.mark.asyncio
    async def test_recharge_card(self, client, db, auth_headers):
        """充值操作"""
        resp = await client.post("/api/v1/members/", json={
            "name": "充值会员",
            "phone": "13900009999",
            "initial_card_type": "stored",
            "initial_card_balance": 100,
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        resp = await client.post(f"/api/v1/cards/{member_id}/recharge", json={
            "amount": 500,
            "count": 0,
            "description": "充值500元",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_type"] == "recharge"
        assert data["amount"] == 500
        assert data["balance_before"] == 100
        assert data["balance_after"] == 600

        member_resp = await client.get(f"/api/v1/members/{member_id}", headers=auth_headers)
        member = member_resp.json()
        assert member["card_balance"] == 600

    @pytest.mark.asyncio
    async def test_upgrade_card(self, client, db, auth_headers):
        """升级卡种"""
        resp = await client.post("/api/v1/members/", json={
            "name": "升级会员",
            "phone": "13900010000",
            "initial_card_type": "monthly",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        resp = await client.post(f"/api/v1/cards/{member_id}/upgrade", json={
            "new_card_type": "yearly",
            "amount": 2500,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_type"] == "upgrade"
        assert data["card_type_after"] == "yearly"

        member_resp = await client.get(f"/api/v1/members/{member_id}", headers=auth_headers)
        assert member_resp.json()["card_type"] == "yearly"

    @pytest.mark.asyncio
    async def test_card_transactions(self, client, db, auth_headers):
        """查询交易记录"""
        resp = await client.post("/api/v1/members/", json={
            "name": "交易会员",
            "phone": "13900010111",
            "initial_card_type": "stored",
            "initial_card_balance": 200,
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        await client.post(f"/api/v1/cards/{member_id}/recharge", json={
            "amount": 300, "description": "充值1",
        }, headers=auth_headers)

        await client.post(f"/api/v1/cards/{member_id}/recharge", json={
            "amount": 200, "description": "充值2",
        }, headers=auth_headers)

        resp = await client.get(f"/api/v1/cards/{member_id}/transactions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert len(data["data"]) >= 2

    @pytest.mark.asyncio
    async def test_expiring_cards(self, client, db, auth_headers):
        """查询即将到期会员"""
        resp = await client.post("/api/v1/members/", json={
            "name": "到期会员",
            "phone": "13900010222",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        now = datetime.utcnow()
        end_date = now + timedelta(days=3)
        await client.put(f"/api/v1/members/{member_id}", json={
            "card_type": "monthly",
            "card_start_date": now.isoformat(),
            "card_end_date": end_date.isoformat(),
        }, headers=auth_headers)

        resp = await client.get("/api/v1/cards/expiring?days=7", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert any(c["member_id"] == member_id for c in data)

    @pytest.mark.asyncio
    async def test_expired_cards(self, client, db, auth_headers):
        """查询已过期会员"""
        resp = await client.post("/api/v1/members/", json={
            "name": "已过期会员",
            "phone": "13900010333",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        now = datetime.utcnow()
        past_end = now - timedelta(days=5)
        past_start = now - timedelta(days=35)
        await client.put(f"/api/v1/members/{member_id}", json={
            "card_type": "monthly",
            "card_start_date": past_start.isoformat(),
            "card_end_date": past_end.isoformat(),
        }, headers=auth_headers)

        resp = await client.get("/api/v1/cards/expired", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert any(m["id"] == member_id for m in data["data"])

    @pytest.mark.asyncio
    async def test_renew_extends_from_current_end(self, client, db, auth_headers):
        """续费从当前到期日延长"""
        now = datetime.utcnow()
        future_end = now + timedelta(days=30)

        resp = await client.post("/api/v1/members/", json={
            "name": "延长期限会员",
            "phone": "13900010444",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        await client.put(f"/api/v1/members/{member_id}", json={
            "card_type": "monthly",
            "card_start_date": now.isoformat(),
            "card_end_date": future_end.isoformat(),
        }, headers=auth_headers)

        await client.post(f"/api/v1/cards/{member_id}/renew", json={
            "card_type": "monthly",
            "duration_days": 30,
            "amount": 300,
        }, headers=auth_headers)

        member_resp = await client.get(f"/api/v1/members/{member_id}", headers=auth_headers)
        member = member_resp.json()
        new_end = datetime.fromisoformat(member["card_end_date"].replace("Z", "+00:00")).replace(tzinfo=None)
        assert new_end > future_end
