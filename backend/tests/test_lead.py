"""潜客 CRM 测试"""
import pytest

from backend.models.lead import Lead, LeadSource, LeadStatus


class TestLeadAPI:
    @pytest.mark.asyncio
    async def test_create_lead(self, client, db, auth_headers):
        resp = await client.post("/api/v1/leads/", json={
            "name": "张三",
            "phone": "13811112222",
            "source": "visit",
            "intent": "fitness",
            "expected_budget": 5000,
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "张三"
        assert data["status"] == "new"

    @pytest.mark.asyncio
    async def test_get_lead(self, client, db, auth_headers):
        lead = Lead(name="李四", phone="13822223333", organization_id=1)
        db.add(lead)
        await db.commit()

        resp = await client.get(f"/api/v1/leads/{lead.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "李四"

    @pytest.mark.asyncio
    async def test_get_lead_not_found(self, client, db, auth_headers):
        resp = await client.get("/api/v1/leads/99999", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_lead(self, client, db, auth_headers):
        lead = Lead(name="王五", phone="13833334444", source=LeadSource.VISIT, organization_id=1)
        db.add(lead)
        await db.commit()

        resp = await client.put(f"/api/v1/leads/{lead.id}", json={
            "status": "contacted",
            "expected_budget": 8000,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "contacted"
        assert data["expected_budget"] == 8000

    @pytest.mark.asyncio
    async def test_delete_lead(self, client, db, auth_headers):
        lead = Lead(name="赵六", phone="13844445555", organization_id=1)
        db.add(lead)
        await db.commit()

        resp = await client.delete(f"/api/v1/leads/{lead.id}", headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get(f"/api/v1/leads/{lead.id}", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_leads_with_filter(self, client, db, auth_headers):
        leads = [
            Lead(name=f"潜客{i}", phone=f"1385555{i:04d}", status=LeadStatus.NEW, organization_id=1)
            for i in range(5)
        ]
        leads.append(Lead(name="已联系", phone="13866660001", status=LeadStatus.CONTACTED, organization_id=1))
        db.add_all(leads)
        await db.commit()

        resp = await client.get("/api/v1/leads/?status=new&limit=10", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["data"]) == 5

    @pytest.mark.asyncio
    async def test_lead_tenant_isolation(self, client, db, auth_headers):
        l1 = Lead(name="机构1潜客", phone="13877770001", organization_id=1)
        l2 = Lead(name="机构2潜客", phone="13877770002", organization_id=2)
        db.add_all([l1, l2])
        await db.commit()

        resp = await client.get("/api/v1/leads/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["name"] == "机构1潜客"
