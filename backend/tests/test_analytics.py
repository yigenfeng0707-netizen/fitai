"""经营分析 API 测试"""
import pytest
from datetime import datetime, timedelta


class TestAnalyticsDashboard:
    @pytest.mark.asyncio
    async def test_dashboard_empty(self, client, auth_headers):
        """无数据时返回空统计"""
        resp = await client.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["revenue"]["today"] == 0
        assert data["revenue"]["week"] == 0
        assert data["revenue"]["month"] == 0
        assert data["members"]["total"] == 0
        assert data["members"]["active"] == 0
        assert data["members"]["new_month"] == 0
        assert data["bookings"]["today"] == 0
        assert data["bookings"]["checked_in_today"] == 0
        assert data["bookings"]["week"] == 0
        assert data["courses"]["top"] == []
        assert data["coaches"]["week_load"] == []

    @pytest.mark.asyncio
    async def test_dashboard_with_data(self, client, db, auth_headers):
        """创建数据后验证统计数据"""
        # 创建会员
        resp = await client.post("/api/v1/members/", json={
            "name": "分析会员",
            "phone": "13900005555",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        # 创建教练
        resp = await client.post("/api/v1/coaches/", json={
            "name": "分析教练",
            "phone": "13900006666",
        }, headers=auth_headers)
        coach_id = resp.json()["id"]

        # 创建课程
        resp = await client.post("/api/v1/courses/", json={
            "name": "分析测试课",
            "course_type": "group",
            "duration_minutes": 60,
            "price": 100,
            "coach_id": coach_id,
        }, headers=auth_headers)
        course_id = resp.json()["id"]

        # 创建排期 (今天)
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
        booking_id = resp.json()["id"]

        # 创建订单
        resp = await client.post("/api/v1/orders/", json={
            "member_id": member_id,
            "amount": 500,
            "actual_amount": 450,
            "subject": "测试订单",
        }, headers=auth_headers)
        order_id = resp.json()["id"]

        # 验证仪表盘
        resp = await client.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["members"]["total"] == 1
        assert data["members"]["active"] >= 1
        assert data["members"]["new_month"] == 1
        assert len(data["members"]["trend"]) == 30

        assert data["bookings"]["today"] >= 1
        assert data["bookings"]["checked_in_today"] == 0
        assert data["bookings"]["week"] >= 1
        assert data["bookings"]["completion_rate"] >= 0

        assert data["revenue"]["today"] == 0  # 订单未支付
        assert data["revenue"]["week"] == 0
        assert data["revenue"]["month"] == 0
        assert len(data["revenue"]["trend"]) == 30

        assert len(data["courses"]["top"]) >= 1
        assert data["courses"]["top"][0]["name"] == "分析测试课"
        assert data["courses"]["top"][0]["booking_count"] >= 1

        assert len(data["coaches"]["week_load"]) >= 1
        assert data["coaches"]["week_load"][0]["name"] == "分析教练"
        assert data["coaches"]["week_load"][0]["class_count"] >= 1

        assert len(data["bookings"]["hour_distribution"]) == 16  # 6:00-21:00

    @pytest.mark.asyncio
    async def test_dashboard_paid_order(self, client, db, auth_headers):
        """已支付订单影响营收统计"""
        resp = await client.post("/api/v1/members/", json={
            "name": "付费会员",
            "phone": "13900007777",
        }, headers=auth_headers)
        member_id = resp.json()["id"]

        # 创建已支付的订单
        resp = await client.post("/api/v1/orders/", json={
            "member_id": member_id,
            "amount": 1000,
            "actual_amount": 900,
            "subject": "付费测试",
        }, headers=auth_headers)
        order_id = resp.json()["id"]

        resp = await client.post(f"/api/v1/orders/{order_id}/pay?payment_method=wechat", headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["revenue"]["today"] >= 900
        assert data["revenue"]["week"] >= 900
        assert data["revenue"]["month"] >= 900
