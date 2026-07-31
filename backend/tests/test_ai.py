"""AI 功能测试"""
import pytest

from backend.models.body_test import BodyTestRecord
from backend.models.member import Member, CardType
from backend.models.course import Course, CourseType
from backend.services.ai import ai_service


class TestBodyTestAPI:
    """体测记录 CRUD + AI 分析"""

    @pytest.mark.asyncio
    async def test_create_body_test(self, client, db, auth_headers):
        member = Member(name="体测会员", phone="13811112222", organization_id=1)
        db.add(member)
        await db.commit()

        payload = {
            "height": 170,
            "weight": 70,
            "body_fat_percentage": 22.5,
            "muscle_mass": 35.0,
            "score": 78,
        }
        resp = await client.post(
            f"/api/v1/ai/members/{member.id}/body-tests",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["member_id"] == member.id
        assert data["height"] == 170
        assert data["score"] == 78

    @pytest.mark.asyncio
    async def test_list_body_tests(self, client, db, auth_headers):
        member = Member(name="列表会员", phone="13822223333", organization_id=1)
        db.add(member)
        await db.commit()

        for i in range(3):
            db.add(BodyTestRecord(member_id=member.id, organization_id=1, weight=60 + i))
        await db.commit()

        resp = await client.get(
            f"/api/v1/ai/members/{member.id}/body-tests",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["data"]) == 3

    @pytest.mark.asyncio
    async def test_analyze_body_test(self, client, db, auth_headers):
        member = Member(name="分析会员", phone="13833334444", organization_id=1)
        db.add(member)
        await db.commit()

        db.add(BodyTestRecord(
            member_id=member.id, organization_id=1,
            weight=80, body_fat_percentage=32, bmi=27, score=55,
        ))
        await db.commit()

        resp = await client.get(
            f"/api/v1/ai/members/{member.id}/body-tests/latest",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["current"]["score"] == 55
        assert len(data["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_no_data(self, client, db, auth_headers):
        member = Member(name="无数据会员", phone="13844445555", organization_id=1)
        db.add(member)
        await db.commit()

        resp = await client.get(
            f"/api/v1/ai/members/{member.id}/body-tests/latest",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["current"] is None

    @pytest.mark.asyncio
    async def test_analyze_with_trends(self, client, db, auth_headers):
        member = Member(name="趋势会员", phone="13855556666", organization_id=1)
        db.add(member)
        await db.commit()

        db.add(BodyTestRecord(member_id=member.id, organization_id=1, weight=80, body_fat_percentage=30, created_at=None))
        db.add(BodyTestRecord(member_id=member.id, organization_id=1, weight=75, body_fat_percentage=28, created_at=None))
        await db.commit()

        resp = await client.get(
            f"/api/v1/ai/members/{member.id}/body-tests/latest",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "weight_change" in data["trends"]
        assert len(data["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_body_test_tenant_isolation(self, client, db, auth_headers):
        m1 = Member(name="机构1会员", phone="13866667777", organization_id=1)
        m2 = Member(name="机构2会员", phone="13877778888", organization_id=2)
        db.add_all([m1, m2])
        await db.commit()

        db.add(BodyTestRecord(member_id=m1.id, organization_id=1, weight=70))
        db.add(BodyTestRecord(member_id=m2.id, organization_id=2, weight=80))
        await db.commit()

        resp = await client.get(
            f"/api/v1/ai/members/{m2.id}/body-tests",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_ai_service_analyze_empty(self, db):
        result = await ai_service.analyze_body_test(db, 9999, 1)
        assert result["current"] is None
        assert "尚无体测数据" in result["suggestions"]


class TestRecommendationAPI:
    """课程推荐"""

    @pytest.mark.asyncio
    async def test_recommend_courses(self, client, db, auth_headers):
        member = Member(
            name="推荐会员", phone="13888889999",
            organization_id=1, level=3,
            card_type=CardType.SINGLE, total_consumption=8000,
        )
        db.add(member)
        await db.commit()

        course = Course(
            name="私教课", course_type=CourseType.PRIVATE,
            price=300, duration_minutes=60, is_active=True,
            max_attendees=1, organization_id=1,
        )
        db.add(course)
        await db.commit()

        resp = await client.get(
            f"/api/v1/ai/members/{member.id}/recommendations",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert data[0]["course_name"] == "私教课"

    @pytest.mark.asyncio
    async def test_recommend_no_member(self, client, db, auth_headers):
        resp = await client.get(
            "/api/v1/ai/members/99999/recommendations",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_ai_service_recommend_empty(self, db):
        result = await ai_service.recommend_courses(db, 9999, 1)
        assert result == []


class TestInsightsAPI:
    """经营洞察"""

    @pytest.mark.asyncio
    async def test_dashboard_insights(self, client, db, auth_headers):
        resp = await client.get(
            "/api/v1/ai/dashboard/insights",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "revenue_today" in data
        assert "active_members" in data
        assert "insights" in data
        assert "top_courses" in data
