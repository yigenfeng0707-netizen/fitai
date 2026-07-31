"""签到中心 API 测试"""
import pytest
from datetime import datetime, timedelta


class TestCheckinCenter:
    @pytest.mark.asyncio
    async def test_checkin_today_empty(self, client, auth_headers):
        """今日无数据应返回空统计"""
        resp = await client.get("/api/v1/bookings/checkin/today", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["schedules"] == []

    @pytest.mark.asyncio
    async def test_checkin_today_with_bookings(self, client, db, auth_headers):
        """创建会员、课程、排期、预约后验证签到数据"""
        # 创建会员
        resp = await client.post("/api/v1/members/", json={
            "name": "签到会员",
            "phone": "13900001111",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        # 创建教练
        resp = await client.post("/api/v1/coaches/", json={
            "name": "签到教练",
            "phone": "13900002222",
        }, headers=auth_headers)
        coach_id = resp.json()["id"]

        # 创建课程
        resp = await client.post("/api/v1/courses/", json={
            "name": "签到测试课",
            "course_type": "group",
            "duration_minutes": 60,
            "price": 100,
            "coach_id": coach_id,
        }, headers=auth_headers)
        course_id = resp.json()["id"]

        # 创建今日排期
        now = datetime.utcnow()
        start = now.replace(hour=10, minute=0, second=0) + timedelta(hours=1)
        end = start + timedelta(hours=1)
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }, headers=auth_headers)
        schedule_id = resp.json()["id"]

        # 创建预约
        resp = await client.post("/api/v1/bookings/", json={
            "member_id": member_id,
            "schedule_id": schedule_id,
        }, headers=auth_headers)
        _booking_id = resp.json()["id"]  # noqa

        # 验证签到数据
        resp = await client.get("/api/v1/bookings/checkin/today", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["pending"] >= 1
        assert len(data["schedules"]) >= 1

        schedule_group = data["schedules"][0]
        assert schedule_group["course_name"] == "签到测试课"
        assert schedule_group["enrolled_count"] >= 1
        assert schedule_group["checked_in_count"] == 0

        booking_item = schedule_group["bookings"][0]
        assert booking_item["member_name"] == "签到会员"
        assert booking_item["member_phone"] == "13900001111"
        assert booking_item["status"] == "pending"

    @pytest.mark.asyncio
    async def test_checkin_flow(self, client, db, auth_headers):
        """完整签到流程"""
        resp = await client.post("/api/v1/members/", json={
            "name": "签到会员2",
            "phone": "13900003333",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        resp = await client.post("/api/v1/courses/", json={
            "name": "签到流程测试",
            "course_type": "private",
            "duration_minutes": 60,
            "price": 200,
        }, headers=auth_headers)
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        start = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if start < now:
            start = now + timedelta(minutes=5)
        end = start + timedelta(hours=1)
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }, headers=auth_headers)
        schedule_id = resp.json()["id"]

        resp = await client.post("/api/v1/bookings/", json={
            "member_id": member_id,
            "schedule_id": schedule_id,
        }, headers=auth_headers)
        booking_id = resp.json()["id"]

        # 签到
        resp = await client.post(f"/api/v1/bookings/{booking_id}/checkin", json={
            "check_in_method": "manual",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "checked_in"

        # 验证签到后统计数据
        resp = await client.get("/api/v1/bookings/checkin/today", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["checked_in"] >= 1
        for s in data["schedules"]:
            for b in s["bookings"]:
                if b["id"] == booking_id:
                    assert b["status"] == "checked_in"
                    assert b["check_in_method"] == "manual"

    @pytest.mark.asyncio
    async def test_checkin_invalid_status(self, client, db, auth_headers):
        """已签到的预约不可重复签到"""
        resp = await client.post("/api/v1/members/", json={
            "name": "签到会员3",
            "phone": "13900004444",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        resp = await client.post("/api/v1/courses/", json={
            "name": "重复签到测试",
            "course_type": "group",
            "duration_minutes": 30,
            "price": 50,
        }, headers=auth_headers)
        course_id = resp.json()["id"]

        now = datetime.utcnow()
        start = now.replace(hour=16, minute=0, second=0, microsecond=0)
        if start < now:
            start = now + timedelta(minutes=5)
        end = start + timedelta(minutes=30)
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }, headers=auth_headers)
        schedule_id = resp.json()["id"]

        resp = await client.post("/api/v1/bookings/", json={
            "member_id": member_id,
            "schedule_id": schedule_id,
        }, headers=auth_headers)
        booking_id = resp.json()["id"]

        # 第一次签到成功
        resp = await client.post(f"/api/v1/bookings/{booking_id}/checkin", json={
            "check_in_method": "qrcode",
        }, headers=auth_headers)
        assert resp.status_code == 200

        # 第二次签到应失败
        resp = await client.post(f"/api/v1/bookings/{booking_id}/checkin", json={
            "check_in_method": "manual",
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "不允许签到" in resp.json()["detail"]
