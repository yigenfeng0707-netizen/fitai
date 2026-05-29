"""排课调度 API 测试"""
import pytest
from datetime import datetime, timedelta


class TestScheduleAPI:
    @pytest.mark.asyncio
    async def test_create_schedule(self, client, db, auth_headers):
        # 先创建课程
        resp = await client.post("/api/v1/courses/", json={
            "name": "瑜伽课",
            "course_type": "group",
            "duration_minutes": 60,
            "max_attendees": 20,
            "price": 100,
        }, headers=auth_headers)
        assert resp.status_code == 200
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        start = now + timedelta(hours=1)
        end = now + timedelta(hours=2)

        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["course_id"] == course_id
        assert data["status"] == "scheduled"
        assert data["course_name"] == "瑜伽课"

    @pytest.mark.asyncio
    async def test_get_schedule(self, client, db, auth_headers):
        # 先创建课程
        resp = await client.post("/api/v1/courses/", json={
            "name": "私教课",
            "course_type": "private",
            "duration_minutes": 60,
            "price": 300,
        }, headers=auth_headers)
        assert resp.status_code == 200
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        start = now + timedelta(hours=1)
        end = now + timedelta(hours=2)
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }, headers=auth_headers)
        schedule_id = resp.json()["id"]

        resp = await client.get(f"/api/v1/courses/schedules/{schedule_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == schedule_id

    @pytest.mark.asyncio
    async def test_update_schedule(self, client, db, auth_headers):
        resp = await client.post("/api/v1/courses/", json={
            "name": "力量训练",
            "course_type": "group",
            "duration_minutes": 45,
            "price": 80,
        }, headers=auth_headers)
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        start = now + timedelta(hours=1)
        end = now + timedelta(hours=2)
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }, headers=auth_headers)
        schedule_id = resp.json()["id"]

        resp = await client.put(f"/api/v1/courses/schedules/{schedule_id}", json={
            "status": "cancelled",
            "notes": "暂停一次",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_delete_schedule(self, client, db, auth_headers):
        resp = await client.post("/api/v1/courses/", json={
            "name": "康复训练",
            "course_type": "private",
            "duration_minutes": 60,
            "price": 400,
        }, headers=auth_headers)
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(hours=2)).isoformat(),
        }, headers=auth_headers)
        schedule_id = resp.json()["id"]

        resp = await client.delete(f"/api/v1/courses/schedules/{schedule_id}", headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get(f"/api/v1/courses/schedules/{schedule_id}", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_schedules_by_date_range(self, client, db, auth_headers):
        resp = await client.post("/api/v1/courses/", json={
            "name": "晨间瑜伽",
            "course_type": "group",
            "duration_minutes": 60,
            "price": 50,
        }, headers=auth_headers)
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        for i in range(3):
            await client.post("/api/v1/courses/schedules/", json={
                "course_id": course_id,
                "start_time": tomorrow.replace(hour=9 + i).isoformat(),
                "end_time": tomorrow.replace(hour=10 + i).isoformat(),
            }, headers=auth_headers)

        resp = await client.get(
            f"/api/v1/courses/schedules/?start_date={now.isoformat()}&end_date={(now + timedelta(days=7)).isoformat()}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3
        assert len(data["data"]) >= 3

    @pytest.mark.asyncio
    async def test_batch_create_schedules(self, client, db, auth_headers):
        resp = await client.post("/api/v1/courses/", json={
            "name": "搏击操",
            "course_type": "group",
            "duration_minutes": 45,
            "price": 60,
        }, headers=auth_headers)
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        schedules = [
            {
                "course_id": course_id,
                "start_time": (now + timedelta(days=i, hours=10)).isoformat(),
                "end_time": (now + timedelta(days=i, hours=11)).isoformat(),
            }
            for i in range(1, 6)
        ]

        resp = await client.post("/api/v1/courses/schedules/batch", json={
            "schedules": schedules,
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "成功创建 5 个排期"

    @pytest.mark.asyncio
    async def test_schedule_tenant_isolation(self, client, db, auth_headers, token):
        # 创建两个独立机构
        from backend.models.organization import Organization
        from backend.crud.auth import UserCRUD
        from backend.core.security import create_access_token

        org_a = Organization(name="ScheduleOrgA", slug="sched-org-a")
        org_b = Organization(name="ScheduleOrgB", slug="sched-org-b")
        db.add_all([org_a, org_b])
        await db.flush()

        user_a = await UserCRUD.create(db, "sched_admin_a", "sched_a@example.com", "pass123", "super_admin", organization_id=org_a.id)
        user_b = await UserCRUD.create(db, "sched_admin_b", "sched_b@example.com", "pass456", "super_admin", organization_id=org_b.id)
        await db.commit()

        token_a = create_access_token(data={"sub": str(user_a.id), "role": "super_admin", "org_id": org_a.id})
        headers_a = {"Authorization": f"Bearer {token_a}"}

        resp = await client.post("/api/v1/courses/", json={
            "name": "课程A",
            "course_type": "group",
            "duration_minutes": 60,
            "price": 100,
        }, headers=headers_a)
        assert resp.status_code == 200, f"创建课程失败: {resp.status_code} {resp.text}"
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(hours=2)).isoformat(),
        }, headers=headers_a)
        schedule_id = resp.json()["id"]

        # 机构B的用户无法访问
        token_b = create_access_token(data={"sub": str(user_b.id), "role": "super_admin", "org_id": org_b.id})
        headers_b = {"Authorization": f"Bearer {token_b}"}

        resp = await client.get(f"/api/v1/courses/schedules/{schedule_id}", headers=headers_b)
        assert resp.status_code == 404
