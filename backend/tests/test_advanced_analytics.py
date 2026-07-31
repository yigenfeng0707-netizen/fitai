"""高级分析 API 测试 - 核心指标报表"""
import pytest
from datetime import date, datetime, timedelta


class TestRevenueAnalysis:
    @pytest.mark.asyncio
    async def test_revenue_analysis_empty(self, client, auth_headers):
        """无数据时营收分析返回零值"""
        resp = await client.get(
            "/api/v1/analytics/advanced/revenue",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overview"]["total_revenue"] == 0
        assert data["overview"]["order_count"] == 0
        assert data["overview"]["avg_order_value"] == 0
        assert data["overview"]["refund_amount"] == 0
        assert data["overview"]["net_revenue"] == 0
        assert data["overview"]["growth_rate"] == 0
        assert data["composition"]["new_purchase"] == 0
        assert data["composition"]["renewal"] == 0
        assert data["composition"]["upgrade"] == 0
        assert data["composition"]["other"] == 0
        assert data["top_products"] == []
        # 趋势应填充31天
        assert len(data["trend"]) == 31

    @pytest.mark.asyncio
    async def test_revenue_analysis_with_data(self, client, db, auth_headers):
        """有数据时营收分析返回正确统计"""
        # 创建会员
        resp = await client.post("/api/v1/members/", json={
            "name": "营收测试会员",
            "phone": "13900009901",
        }, headers=auth_headers)
        assert resp.status_code == 200
        member_id = resp.json()["id"]

        # 创建已支付订单
        resp = await client.post("/api/v1/orders/", json={
            "member_id": member_id,
            "amount": 5000,
            "actual_amount": 4500,
            "subject": "新购年卡",
        }, headers=auth_headers)
        assert resp.status_code == 201
        order_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/orders/{order_id}/pay?payment_method=wechat",
            headers=auth_headers,
        )
        assert resp.status_code == 200

        today = date.today().strftime("%Y-%m-%d")
        resp = await client.get(
            "/api/v1/analytics/advanced/revenue",
            params={"start_date": today, "end_date": today},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overview"]["total_revenue"] >= 4500
        assert data["overview"]["order_count"] >= 1
        assert data["overview"]["avg_order_value"] >= 4500
        assert len(data["trend"]) == 1
        assert len(data["top_products"]) >= 1

    @pytest.mark.asyncio
    async def test_revenue_analysis_group_by_week(self, client, auth_headers):
        """按周分组营收趋势"""
        resp = await client.get(
            "/api/v1/analytics/advanced/revenue",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "group_by": "week"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["trend"], list)

    @pytest.mark.asyncio
    async def test_revenue_analysis_group_by_month(self, client, auth_headers):
        """按月分组营收趋势"""
        resp = await client.get(
            "/api/v1/analytics/advanced/revenue",
            params={"start_date": "2026-01-01", "end_date": "2026-03-31", "group_by": "month"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["trend"], list)


class TestMemberAnalysis:
    @pytest.mark.asyncio
    async def test_member_analysis_empty(self, client, auth_headers):
        """无数据时会员分析返回零值"""
        resp = await client.get(
            "/api/v1/analytics/advanced/members",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overview"]["total_members"] == 0
        assert data["overview"]["new_members"] == 0
        assert data["overview"]["active_members"] == 0
        assert data["overview"]["churned_members"] == 0
        assert data["overview"]["net_growth"] == 0
        assert data["overview"]["growth_rate"] == 0
        assert data["avg_consumption"] == 0
        assert data["distribution"]["by_level"] == {}
        assert data["distribution"]["by_card_type"] == {}
        assert data["distribution"]["by_source"] == {}
        assert data["distribution"]["by_store"] == []
        assert len(data["trend"]) == 31

    @pytest.mark.asyncio
    async def test_member_analysis_with_data(self, client, db, auth_headers):
        """有数据时会员分析返回正确统计"""
        resp = await client.post("/api/v1/members/", json={
            "name": "会员分析测试",
            "phone": "13900009902",
        }, headers=auth_headers)
        assert resp.status_code == 200

        today = date.today().strftime("%Y-%m-%d")
        resp = await client.get(
            "/api/v1/analytics/advanced/members",
            params={"start_date": today, "end_date": today},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overview"]["total_members"] >= 1
        assert data["overview"]["new_members"] >= 1


class TestCourseAnalysis:
    @pytest.mark.asyncio
    async def test_course_analysis_empty(self, client, auth_headers):
        """无数据时课程分析返回空列表"""
        resp = await client.get(
            "/api/v1/analytics/advanced/courses",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["top_courses"] == []
        assert data["type_distribution"] == {}
        assert data["avg_fill_rate"] == 0
        # 时段分布应有16个时段 (6:00-21:00)
        assert len(data["time_slot_distribution"]) == 16

    @pytest.mark.asyncio
    async def test_course_analysis_with_data(self, client, db, auth_headers):
        """有数据时课程分析返回正确统计"""
        # 创建教练
        resp = await client.post("/api/v1/coaches/", json={
            "name": "课程分析教练",
            "phone": "13900009903",
        }, headers=auth_headers)
        assert resp.status_code == 200
        coach_id = resp.json()["id"]

        # 创建课程
        resp = await client.post("/api/v1/courses/", json={
            "name": "课程分析测试课",
            "course_type": "group",
            "duration_minutes": 60,
            "price": 100,
            "coach_id": coach_id,
            "max_attendees": 20,
        }, headers=auth_headers)
        assert resp.status_code == 200
        course_id = resp.json()["id"]

        # 创建排期
        now = datetime.utcnow()
        start = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(hours=1)
        end = start + timedelta(hours=1)
        resp = await client.post("/api/v1/courses/schedules/", json={
            "course_id": course_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }, headers=auth_headers)
        assert resp.status_code == 200

        today = date.today().strftime("%Y-%m-%d")
        resp = await client.get(
            "/api/v1/analytics/advanced/courses",
            params={"start_date": today, "end_date": today},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["top_courses"]) >= 1
        assert data["top_courses"][0]["name"] == "课程分析测试课"


class TestCoachPerformance:
    @pytest.mark.asyncio
    async def test_coach_performance_empty(self, client, auth_headers):
        """无教练时返回空列表"""
        resp = await client.get(
            "/api/v1/analytics/advanced/coaches",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_coach_performance_with_data(self, client, db, auth_headers):
        """有教练时返回绩效数据"""
        resp = await client.post("/api/v1/coaches/", json={
            "name": "绩效教练",
            "phone": "13900009904",
        }, headers=auth_headers)
        assert resp.status_code == 200

        today = date.today().strftime("%Y-%m-%d")
        resp = await client.get(
            "/api/v1/analytics/advanced/coaches",
            params={"start_date": today, "end_date": today},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        coach = data[0]
        assert "coach_id" in coach
        assert "coach_name" in coach
        assert "classes_taught" in coach
        assert "total_students" in coach
        assert "avg_rating" in coach
        assert "revenue_contribution" in coach
        assert "utilization_rate" in coach


class TestConversionFunnel:
    @pytest.mark.asyncio
    async def test_conversion_funnel_empty(self, client, auth_headers):
        """无数据时转化漏斗返回零值"""
        resp = await client.get(
            "/api/v1/analytics/advanced/funnel",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["leads"] == 0
        assert data["trials"] == 0
        assert data["conversions"] == 0
        assert data["renewals"] == 0
        assert data["referrals"] == 0
        assert data["lead_to_trial_rate"] == 0
        assert data["trial_to_conversion_rate"] == 0
        assert data["conversion_to_renewal_rate"] == 0

    @pytest.mark.asyncio
    async def test_conversion_funnel_with_leads(self, client, db, auth_headers):
        """有潜客数据时转化漏斗返回正确统计"""
        # 创建潜客
        resp = await client.post("/api/v1/leads/", json={
            "name": "漏斗测试潜客",
            "phone": "13900009905",
            "source": "visit",
        }, headers=auth_headers)
        assert resp.status_code == 201

        today = date.today().strftime("%Y-%m-%d")
        resp = await client.get(
            "/api/v1/analytics/advanced/funnel",
            params={"start_date": today, "end_date": today},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["leads"] >= 1


class TestStoreComparison:
    @pytest.mark.asyncio
    async def test_store_comparison_empty(self, client, auth_headers):
        """无门店时返回空列表"""
        resp = await client.get(
            "/api/v1/analytics/advanced/stores",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data == []


class TestRequiresAuth:
    @pytest.mark.asyncio
    async def test_revenue_requires_auth(self, client):
        """营收分析接口需要认证"""
        resp = await client.get(
            "/api/v1/analytics/advanced/revenue",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_members_requires_auth(self, client):
        """会员分析接口需要认证"""
        resp = await client.get(
            "/api/v1/analytics/advanced/members",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_courses_requires_auth(self, client):
        """课程分析接口需要认证"""
        resp = await client.get(
            "/api/v1/analytics/advanced/courses",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_coaches_requires_auth(self, client):
        """教练绩效接口需要认证"""
        resp = await client.get(
            "/api/v1/analytics/advanced/coaches",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_funnel_requires_auth(self, client):
        """转化漏斗接口需要认证"""
        resp = await client.get(
            "/api/v1/analytics/advanced/funnel",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_stores_requires_auth(self, client):
        """门店对比接口需要认证"""
        resp = await client.get(
            "/api/v1/analytics/advanced/stores",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert resp.status_code == 401
