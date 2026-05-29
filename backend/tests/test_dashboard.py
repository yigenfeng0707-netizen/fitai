"""数据可视化仪表盘 API 测试"""
import pytest
from datetime import datetime, timedelta


class TestExecutiveDashboard:
    @pytest.mark.asyncio
    async def test_executive_dashboard_empty(self, client, auth_headers):
        """无数据时高管仪表盘返回默认值"""
        resp = await client.get(
            "/api/v1/dashboard/executive",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()

        # KPI 检查
        assert "kpi" in data
        assert data["kpi"]["total_revenue"]["value"] == 0
        assert data["kpi"]["total_members"]["value"] == 0
        assert data["kpi"]["today_bookings"]["value"] == 0
        assert data["kpi"]["checkin_rate"]["value"] == 0
        assert data["kpi"]["active_stores"]["value"] == 0

        # 图表检查
        assert "revenue_chart" in data
        assert data["revenue_chart"]["chart_type"] == "line"
        assert len(data["revenue_chart"]["data"]) == 30

        assert "member_chart" in data
        assert data["member_chart"]["chart_type"] == "bar"
        assert len(data["member_chart"]["data"]) == 30

        assert "booking_chart" in data
        assert data["booking_chart"]["chart_type"] == "line"
        assert len(data["booking_chart"]["data"]) == 30

        # 排名和课程
        assert data["store_ranking"] == []
        assert data["top_courses"] == []

        # 预警
        assert isinstance(data["alerts"], list)

    @pytest.mark.asyncio
    async def test_executive_dashboard_with_data(self, client, db, auth_headers):
        """创建数据后验证高管仪表盘"""
        # 创建门店
        resp = await client.post("/api/v1/stores/", json={
            "name": "测试门店A",
            "code": "TSTA",
            "address": "测试地址",
        }, headers=auth_headers)
        assert resp.status_code in (200, 201)
        store_id = resp.json()["id"]

        # 创建会员
        resp = await client.post("/api/v1/members/", json={
            "name": "仪表盘会员",
            "phone": "13900008888",
            "store_id": store_id,
        }, headers=auth_headers)
        assert resp.status_code in (200, 201)
        member_id = resp.json()["id"]

        # 创建教练
        resp = await client.post("/api/v1/coaches/", json={
            "name": "仪表盘教练",
            "phone": "13900009999",
            "store_id": store_id,
        }, headers=auth_headers)
        assert resp.status_code in (200, 201)
        coach_id = resp.json()["id"]

        # 创建课程
        resp = await client.post("/api/v1/courses/", json={
            "name": "仪表盘测试课",
            "course_type": "group",
            "duration_minutes": 60,
            "price": 100,
            "coach_id": coach_id,
        }, headers=auth_headers)
        assert resp.status_code in (200, 201)
        course_id = resp.json()["id"]

        # 创建排期 (今天)
        now = datetime.utcnow()
        start = now.replace(hour=10, minute=0, second=0) + timedelta(hours=1)
        end = start + timedelta(hours=1)
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "store_id": store_id,
        }, headers=auth_headers)
        assert resp.status_code in (200, 201)
        schedule_id = resp.json()["id"]

        # 创建预约
        resp = await client.post("/api/v1/bookings/", json={
            "member_id": member_id,
            "schedule_id": schedule_id,
        }, headers=auth_headers)
        assert resp.status_code in (200, 201)

        # 创建已支付订单
        resp = await client.post("/api/v1/orders/", json={
            "member_id": member_id,
            "amount": 1000,
            "actual_amount": 900,
            "subject": "仪表盘测试订单",
            "store_id": store_id,
        }, headers=auth_headers)
        assert resp.status_code in (200, 201)
        order_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/orders/{order_id}/pay?payment_method=wechat",
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # 验证高管仪表盘
        resp = await client.get(
            "/api/v1/dashboard/executive",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["kpi"]["total_revenue"]["value"] >= 900
        assert data["kpi"]["total_members"]["value"] >= 1
        assert data["kpi"]["today_bookings"]["value"] >= 1
        assert data["kpi"]["active_stores"]["value"] >= 1

        assert len(data["top_courses"]) >= 1
        assert data["top_courses"][0]["name"] == "仪表盘测试课"

        assert len(data["store_ranking"]) >= 1

    @pytest.mark.asyncio
    async def test_executive_dashboard_period(self, client, auth_headers):
        """不同周期参数"""
        for period in ["today", "week", "month", "quarter", "year"]:
            resp = await client.get(
                "/api/v1/dashboard/executive",
                params={"period": period},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "kpi" in data
            assert "revenue_chart" in data


class TestStoreDashboard:
    @pytest.mark.asyncio
    async def test_store_dashboard(self, client, auth_headers):
        """门店仪表盘 - 无数据"""
        # 先创建一个门店
        resp = await client.post("/api/v1/stores/", json={
            "name": "门店仪表盘测试",
            "code": "DASH01",
        }, headers=auth_headers)
        assert resp.status_code in (200, 201)
        store_id = resp.json()["id"]

        resp = await client.get(
            f"/api/v1/dashboard/store/{store_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "kpi" in data
        assert data["kpi"]["total_revenue"]["value"] == 0
        assert data["kpi"]["store_members"]["value"] == 0
        assert data["kpi"]["today_bookings"]["value"] == 0
        assert data["kpi"]["today_checkins"]["value"] == 0

        assert "today_schedule" in data
        assert isinstance(data["today_schedule"], list)

        assert "revenue_chart" in data
        assert len(data["revenue_chart"]["data"]) == 30

        assert "member_chart" in data
        assert len(data["member_chart"]["data"]) == 30

        assert "coach_performance" in data
        assert isinstance(data["coach_performance"], list)

        assert "hourly_distribution" in data
        assert data["hourly_distribution"]["chart_type"] == "bar"


class TestRealtimeData:
    @pytest.mark.asyncio
    async def test_realtime_data(self, client, auth_headers):
        """实时数据接口"""
        resp = await client.get(
            "/api/v1/dashboard/realtime",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "today_stats" in data
        assert "revenue" in data["today_stats"]
        assert "bookings" in data["today_stats"]
        assert "checkins" in data["today_stats"]

        assert "ongoing_classes" in data
        assert isinstance(data["ongoing_classes"], list)

        assert "upcoming_classes" in data
        assert isinstance(data["upcoming_classes"], list)

        assert "staff_online" in data
        assert isinstance(data["staff_online"], int)

        assert "alerts" in data
        assert isinstance(data["alerts"], list)


class TestYearOverYear:
    @pytest.mark.asyncio
    async def test_year_over_year(self, client, auth_headers):
        """同比分析接口"""
        for metric in ["revenue", "members", "bookings"]:
            resp = await client.get(
                "/api/v1/dashboard/year-over-year",
                params={"metric": metric},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()

            assert "current_year" in data
            assert "previous_year" in data
            assert "months" in data

            assert len(data["current_year"]) == 12
            assert len(data["previous_year"]) == 12
            assert len(data["months"]) == 12

            # 每个数据点有 label 和 value
            for point in data["current_year"]:
                assert "label" in point
                assert "value" in point


class TestAlerts:
    @pytest.mark.asyncio
    async def test_alerts(self, client, auth_headers):
        """预警信息接口"""
        resp = await client.get(
            "/api/v1/dashboard/alerts",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

        # 每条预警有必要的字段
        for alert in data:
            assert "type" in alert
            assert "title" in alert
            assert "message" in alert
            assert "count" in alert
            assert alert["type"] in ("warning", "danger", "info")


class TestAuthRequired:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client):
        """未认证访问应返回 401"""
        endpoints = [
            "/api/v1/dashboard/executive",
            "/api/v1/dashboard/store/1",
            "/api/v1/dashboard/realtime",
            "/api/v1/dashboard/year-over-year",
            "/api/v1/dashboard/alerts",
        ]
        for endpoint in endpoints:
            resp = await client.get(endpoint)
            assert resp.status_code == 401


class TestInvalidPeriod:
    @pytest.mark.asyncio
    async def test_invalid_period(self, client, auth_headers):
        """无效的 period 参数应返回 422"""
        resp = await client.get(
            "/api/v1/dashboard/executive",
            params={"period": "invalid"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_metric(self, client, auth_headers):
        """无效的 metric 参数应返回 422"""
        resp = await client.get(
            "/api/v1/dashboard/year-over-year",
            params={"metric": "invalid"},
            headers=auth_headers,
        )
        assert resp.status_code == 422
