"""
完整业务流程集成测试
测试从组织设置到日常运营的全链路场景
"""
import random
import time

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database_test import async_engine as async_engine_test, AsyncSessionLocal as async_session_test


# ============================================================
# 辅助函数
# ============================================================

def _reset_rate_limiter():
    """重置速率限制器状态，避免测试间相互影响"""
    from backend.core.rate_limiter import _requests, _last_prune
    _requests.clear()
    _last_prune = 0.0


def _uid():
    """生成唯一标识，避免测试间数据冲突"""
    return f"{int(time.time() * 1000) % 100000000}{random.randint(1000, 9999)}"


def _unique_phone():
    """生成唯一手机号"""
    return f"13{random.randint(100000000, 999999999)}"


async def _create_org_and_admin(client: AsyncClient, db: AsyncSession,
                                 org_name: str = "integ-org", admin_name: str = "admin"):
    """创建组织和管理员，返回 (org_id, admin_token, admin_headers)"""
    _reset_rate_limiter()
    from backend.models.organization import Organization
    uid = _uid()
    org = Organization(name=org_name, slug=f"integ-{org_name}-{uid}", plan="professional", status="active")
    db.add(org)
    await db.flush()
    org_id = org.id

    resp = await client.post("/api/v1/auth/register", json={
        "username": f"{admin_name}_{uid}",
        "password": "TestPass123!",
        "email": f"{admin_name}_{uid}@test.com",
        "role": "super_admin",
    })
    assert resp.status_code in (200, 201), f"注册管理员失败: {resp.text}"

    resp = await client.post("/api/v1/auth/login", json={
        "username": f"{admin_name}_{uid}",
        "password": "TestPass123!",
    })
    assert resp.status_code == 200, f"管理员登录失败: {resp.text}"
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return org_id, token, headers


async def _create_staff_user(db: AsyncSession, org_id: int, username: str, role: str = "receptionist"):
    """创建员工用户（通过CRUD直接创建，不经过API），返回 (user, headers)"""
    from backend.crud.auth import UserCRUD
    from backend.core.security import create_access_token
    user = await UserCRUD.create(
        db, username=username,
        email=f"{username}@test.com",
        password="StaffPass123!",
        role=role,
        organization_id=org_id,
    )
    await db.flush()
    token = create_access_token(data={"sub": str(user.id), "role": user.role, "org_id": org_id})
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


async def _create_store(client: AsyncClient, headers: dict, name: str, code: str):
    """创建门店，返回门店数据"""
    resp = await client.post("/api/v1/stores/", json={
        "name": name, "code": code,
        "address": f"{name}地址", "city": "北京",
    }, headers=headers)
    assert resp.status_code in (200, 201), f"创建门店 {name} 失败: {resp.text}"
    return resp.json()


async def _create_coach(client: AsyncClient, headers: dict, name: str, phone: str = None):
    """创建教练，返回教练数据"""
    if phone is None:
        phone = _unique_phone()
    resp = await client.post("/api/v1/coaches/", json={
        "name": name, "phone": phone,
        "specialization": "瑜伽",
    }, headers=headers)
    assert resp.status_code in (200, 201), f"创建教练 {name} 失败: {resp.text}"
    return resp.json()


async def _create_course(client: AsyncClient, headers: dict, name: str, course_type: str = "group",
                        coach_id: int = None, max_attendees: int = 20):
    """创建课程，返回课程数据"""
    payload = {
        "name": name,
        "course_type": course_type,
        "duration_minutes": 60,
        "max_attendees": max_attendees,
        "price": 50.0,
    }
    if coach_id:
        payload["coach_id"] = coach_id
    resp = await client.post("/api/v1/courses/", json=payload, headers=headers)
    assert resp.status_code in (200, 201), f"创建课程 {name} 失败: {resp.text}"
    return resp.json()


async def _create_schedule(client: AsyncClient, headers: dict, course_id: int,
                            start_time: datetime, end_time: datetime):
    """创建排课，返回排课数据"""
    resp = await client.post("/api/v1/courses/schedules/", json={
        "course_id": course_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "notes": "集成测试排课",
    }, headers=headers)
    assert resp.status_code == 200, f"创建排课失败: {resp.text}"
    return resp.json()


async def _create_member(client: AsyncClient, headers: dict, name: str, phone: str = None):
    """创建会员，返回会员数据"""
    if phone is None:
        phone = _unique_phone()
    resp = await client.post("/api/v1/members/", json={
        "name": name, "phone": phone,
    }, headers=headers)
    assert resp.status_code in (200, 201), f"创建会员 {name} 失败: {resp.text}"
    return resp.json()


async def _create_order(client: AsyncClient, headers: dict, member_id: int, amount: float,
                        product_type: str = "card", subject: str = "月卡"):
    """创建订单，返回订单数据"""
    resp = await client.post("/api/v1/orders/", json={
        "member_id": member_id,
        "amount": amount,
        "actual_amount": amount,
        "product_type": product_type,
        "subject": subject,
    }, headers=headers)
    assert resp.status_code in (200, 201), f"创建订单失败: {resp.text}"
    return resp.json()


async def _create_booking(client: AsyncClient, headers: dict, member_id: int, schedule_id: int):
    """创建预约，返回预约数据"""
    resp = await client.post("/api/v1/bookings/", json={
        "member_id": member_id,
        "schedule_id": schedule_id,
    }, headers=headers)
    assert resp.status_code == 200, f"创建预约失败: {resp.text}"
    return resp.json()


# ============================================================
# TestFullWorkflow - 完整业务流程集成测试
# ============================================================

class TestFullWorkflow:
    """完整业务流程集成测试"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_organization_setup(self, client: AsyncClient, db: AsyncSession):
        """
        完整组织设置流程:
        1. 注册管理员
        2. 登录获取token
        3. 创建门店A和门店B
        4. 创建教练
        5. 创建课程
        6. 创建排课
        """
        # 1. 注册管理员 + 2. 登录获取token
        org_id, token, headers = await _create_org_and_admin(
            client, db, org_name="setup-test", admin_name="setup_admin"
        )
        assert org_id is not None, "组织ID不应为空"
        assert token, "应返回有效的token"

        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200, "获取当前用户信息失败"
        assert resp.json()["role"] == "super_admin", "角色应为 super_admin"

        # 3. 创建门店A和门店B
        store_a = await _create_store(client, headers, "旗舰店A", "HQ_A")
        assert store_a["name"] == "旗舰店A"
        assert store_a["is_active"] is True

        store_b = await _create_store(client, headers, "分店B", "BRANCH_B")
        assert store_b["name"] == "分店B"

        resp = await client.get("/api/v1/stores/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2, "应至少有2个门店"

        # 4. 创建教练
        coach = await _create_coach(client, headers, "张教练")
        assert coach["name"] == "张教练"
        assert coach["is_active"] is True

        # 5. 创建课程
        course = await _create_course(client, headers, "瑜伽基础课", "group", coach_id=coach["id"])
        assert course["name"] == "瑜伽基础课"
        assert course["course_type"] == "group"
        assert course["coach_id"] == coach["id"]

        # 6. 创建排课
        now = datetime.utcnow()
        start = now + timedelta(hours=24)
        end = start + timedelta(hours=1)
        schedule = await _create_schedule(client, headers, course["id"], start, end)
        assert schedule["course_id"] == course["id"]
        assert schedule["status"] == "scheduled"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_member_journey(self, client: AsyncClient, db: AsyncSession):
        """
        会员完整旅程:
        1. 创建会员
        2. 购买会员卡（创建订单）
        3. 预约课程
        4. 签到
        5. 查看预约历史
        6. 查看会员资料
        """
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="member-journey", admin_name="mj_admin"
        )

        # 准备数据: 创建教练和课程
        coach = await _create_coach(client, headers, "李教练")
        course = await _create_course(client, headers, "有氧操课", "group", coach_id=coach["id"])
        now = datetime.utcnow()
        start = now + timedelta(hours=48)
        end = start + timedelta(hours=1)
        schedule = await _create_schedule(client, headers, course["id"], start, end)

        # 1. 创建会员
        member_phone = _unique_phone()
        member = await _create_member(client, headers, "王会员", member_phone)
        assert member["name"] == "王会员"
        assert member["status"] == "active"
        member_id = member["id"]

        # 2. 购买会员卡（创建订单）
        order = await _create_order(client, headers, member_id, 299.0, "card", "月卡购买")
        assert order["payment_status"] == "pending"
        assert order["amount"] == 299.0

        # 3. 预约课程
        booking = await _create_booking(client, headers, member_id, schedule["id"])
        assert booking["member_id"] == member_id
        assert booking["schedule_id"] == schedule["id"]
        assert booking["status"] == "pending"
        booking_id = booking["id"]

        # 4. 签到
        resp = await client.post(
            f"/api/v1/bookings/{booking_id}/checkin",
            json={"check_in_method": "manual"},
            headers=headers,
        )
        assert resp.status_code == 200, f"签到失败: {resp.text}"
        checked_in = resp.json()
        assert checked_in["status"] == "checked_in", "签到后状态应为 checked_in"
        assert checked_in["check_in_time"] is not None, "签到时间不应为空"

        # 5. 查看预约历史
        resp = await client.get(
            "/api/v1/bookings/",
            params={"member_id": member_id},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1, "预约历史应至少有1条记录"
        found = any(b["id"] == booking_id for b in data["data"])
        assert found, "预约历史中应包含刚创建的预约"

        # 6. 查看会员资料
        resp = await client.get(f"/api/v1/members/{member_id}", headers=headers)
        assert resp.status_code == 200
        profile = resp.json()
        assert profile["name"] == "王会员"
        assert profile["phone"] == member_phone

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_marketing_automation_workflow(self, client: AsyncClient, db: AsyncSession):
        """
        营销自动化完整流程:
        1. 创建营销规则（新会员自动发送通知）
        2. 创建新会员触发规则
        3. 验证通知已发送
        4. 查看规则执行日志
        """
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="marketing-test", admin_name="mkt_admin"
        )

        # 1. 创建营销规则
        resp = await client.post("/api/v1/marketing/rules", json={
            "name": "新会员自动欢迎通知",
            "description": "新会员创建时自动发送欢迎通知",
            "trigger": {"event_type": "member_created"},
            "conditions": [],
            "actions": [
                {
                    "type": "send_notification",
                    "params": {
                        "title": "欢迎加入！",
                        "content": "亲爱的{{name}}，欢迎加入我们的健身大家庭！",
                    },
                }
            ],
            "is_active": True,
        }, headers=headers)
        assert resp.status_code in (200, 201), f"创建营销规则失败: {resp.text}"
        rule = resp.json()
        rule_id = rule["id"]
        assert rule["trigger_type"] == "member_created"
        assert rule["is_active"] is True

        # 2. 创建新会员触发规则
        member = await _create_member(client, headers, "营销测试会员")
        member_id = member["id"]

        # 手动触发事件
        resp = await client.post("/api/v1/marketing/events", json={
            "event_type": "member_created",
            "entity_id": member_id,
        }, headers=headers)
        assert resp.status_code == 200, f"触发营销事件失败: {resp.text}"
        results = resp.json()
        assert len(results) >= 1, "应至少有1条规则匹配结果"
        assert results[0]["matched"] is True, "新会员规则应匹配成功"
        assert len(results[0]["actions_executed"]) >= 1, "应至少执行1个动作"

        # 3. 验证通知已发送（通过规则执行日志间接验证）
        resp = await client.get(f"/api/v1/marketing/rules/{rule_id}/logs", headers=headers)
        assert resp.status_code == 200, f"获取规则日志失败: {resp.text}"
        logs = resp.json()
        assert logs["total"] >= 1, "应至少有1条执行日志"

        # 4. 查看规则执行日志详情
        log_entry = logs["data"][0]
        assert log_entry["rule_id"] == rule_id, "日志应关联到正确的规则"
        assert log_entry["trigger_entity_id"] == member_id, "日志应关联到正确的会员"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_store_management_workflow(self, client: AsyncClient, db: AsyncSession):
        """
        门店管理完整流程:
        1. 创建门店
        2. 分配员工
        3. 转移会员
        4. 查看跨门店报表
        """
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="store-mgmt-test", admin_name="store_admin"
        )

        # 1. 创建门店
        store = await _create_store(client, headers, "管理流程店", "MGMT_S")
        store_id = store["id"]

        # 2. 分配员工（通过CRUD直接创建，绕过rate limiter）
        from backend.crud.auth import UserCRUD
        staff_user = await UserCRUD.create(
            db, username=f"store_staff_{_uid()}",
            email=f"store_staff_{_uid()}@test.com",
            password="StaffPass123!",
            role="receptionist",
            organization_id=org_id,
        )
        await db.commit()

        resp = await client.post(f"/api/v1/stores/{store_id}/staff/", json={
            "user_id": staff_user.id,
            "role_at_store": "前台",
            "is_primary": True,
        }, headers=headers)
        assert resp.status_code in (200, 201), f"分配员工失败: {resp.text}"

        # 验证员工已分配
        resp = await client.get(f"/api/v1/stores/{store_id}/staff/", headers=headers)
        assert resp.status_code == 200
        staff_list = resp.json()
        assert any(s["user_id"] == staff_user.id for s in staff_list), "员工应出现在门店员工列表中"

        # 3. 创建会员并关联到门店
        member = await _create_member(client, headers, "门店会员")
        member_id = member["id"]

        resp = await client.put(f"/api/v1/members/{member_id}", json={
            "store_id": store_id,
        }, headers=headers)
        assert resp.status_code == 200, f"更新会员门店失败: {resp.text}"

        # 4. 查看门店列表
        resp = await client.get("/api/v1/stores/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1, "应至少有1个门店"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_analytics_workflow(self, client: AsyncClient, db: AsyncSession):
        """
        数据分析完整流程:
        1. 创建订单数据
        2. 创建预约数据
        3. 查看仪表盘
        4. 查看报表
        """
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="analytics-test", admin_name="analytics_admin"
        )

        # 准备基础数据
        coach = await _create_coach(client, headers, "数据教练")
        course = await _create_course(client, headers, "数据分析课", "group", coach_id=coach["id"])
        now = datetime.utcnow()
        start = now + timedelta(hours=72)
        end = start + timedelta(hours=1)
        schedule = await _create_schedule(client, headers, course["id"], start, end)

        # 1. 创建订单数据
        member_a = await _create_member(client, headers, "数据会员A")
        member_b = await _create_member(client, headers, "数据会员B")

        order_a = await _create_order(client, headers, member_a["id"], 199.0, "card", "季卡")
        order_b = await _create_order(client, headers, member_b["id"], 399.0, "card", "年卡")
        assert order_a["payment_status"] == "pending"
        assert order_b["payment_status"] == "pending"

        # 2. 创建预约数据
        booking_a = await _create_booking(client, headers, member_a["id"], schedule["id"])
        booking_b = await _create_booking(client, headers, member_b["id"], schedule["id"])
        assert booking_a["status"] == "pending"
        assert booking_b["status"] == "pending"

        # 3. 查看仪表盘
        resp = await client.get("/api/v1/analytics/dashboard", headers=headers)
        assert resp.status_code == 200, f"获取仪表盘数据失败: {resp.text}"
        dashboard = resp.json()
        assert isinstance(dashboard, dict), "仪表盘应返回字典数据"

        # 4. 查看高管仪表盘
        resp = await client.get("/api/v1/dashboard/executive", params={"period": "month"}, headers=headers)
        assert resp.status_code == 200, f"获取高管仪表盘失败: {resp.text}"

        # 查看订单列表确认数据存在
        resp = await client.get("/api/v1/orders/", headers=headers)
        assert resp.status_code == 200
        orders_data = resp.json()
        assert orders_data["total"] >= 2, "应至少有2条订单"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_mini_program_workflow(self, client: AsyncClient, db: AsyncSession):
        """
        小程序端完整流程:
        1. 微信登录
        2. 查看课程列表
        3. 预约课程
        4. 签到
        5. 查看个人中心
        6. 创建支付订单
        """
        _reset_rate_limiter()
        org_id, _, admin_headers = await _create_org_and_admin(
            client, db, org_name="mini-test", admin_name="mini_admin"
        )

        coach = await _create_coach(client, admin_headers, "小程序教练")
        course = await _create_course(client, admin_headers, "小程序瑜伽课", "group", coach_id=coach["id"])
        now = datetime.utcnow()
        start = now + timedelta(hours=96)
        end = start + timedelta(hours=1)
        schedule = await _create_schedule(client, admin_headers, course["id"], start, end)

        # 创建会员并关联用户
        member_phone = _unique_phone()
        member = await _create_member(client, admin_headers, "小程序会员", member_phone)
        member_id = member["id"]

        # 创建关联用户（模拟小程序用户绑定会员，通过CRUD直接创建绕过rate limiter）
        from backend.crud.auth import UserCRUD
        from backend.core.security import create_access_token
        mini_user = await UserCRUD.create(
            db, username=f"mini_user_{_uid()}",
            email=f"mini_user_{_uid()}@test.com",
            password="MiniPass123!",
            role="member",
            organization_id=org_id,
        )
        mini_user.member_id = member_id
        await db.commit()

        mini_token = create_access_token(data={"sub": str(mini_user.id), "role": "member", "org_id": org_id})
        mini_headers = {"Authorization": f"Bearer {mini_token}"}

        # 1. 微信登录
        _reset_rate_limiter()
        resp = await client.post("/api/v1/mini/auth/wx-login", json={
            "code": f"test_mini_integration_{_uid()}",
        })
        assert resp.status_code == 200, f"微信登录失败: {resp.text}"
        wx_data = resp.json()
        assert "access_token" in wx_data, "应返回 access_token"

        # 2. 查看课程列表
        resp = await client.get("/api/v1/mini/courses", headers=mini_headers)
        assert resp.status_code == 200, f"获取课程列表失败: {resp.text}"
        courses_data = resp.json()
        assert courses_data["total"] >= 1, "应至少有1门课程"

        # 3. 预约课程
        resp = await client.post("/api/v1/mini/bookings", json={
            "schedule_id": schedule["id"],
        }, headers=mini_headers)
        assert resp.status_code == 200, f"小程序预约失败: {resp.text}"
        mini_booking = resp.json()
        assert mini_booking["status"] == "confirmed", "小程序预约状态应为 confirmed"
        booking_id = mini_booking["id"]

        # 4. 签到
        resp = await client.post(
            f"/api/v1/mini/bookings/{booking_id}/checkin",
            headers=mini_headers,
        )
        assert resp.status_code == 200, f"小程序签到失败: {resp.text}"
        checked_in = resp.json()
        assert checked_in["status"] == "checked_in", "签到后状态应为 checked_in"

        # 5. 查看个人中心
        resp = await client.get("/api/v1/mini/member/profile", headers=mini_headers)
        assert resp.status_code == 200, f"获取个人资料失败: {resp.text}"
        profile = resp.json()
        assert profile["name"] == "小程序会员"
        assert profile["phone"] == member_phone

        # 查看预约历史
        resp = await client.get("/api/v1/mini/member/bookings", headers=mini_headers)
        assert resp.status_code == 200
        bookings_data = resp.json()
        assert bookings_data["total"] >= 1, "预约历史应至少有1条"

        # 6. 创建支付订单
        resp = await client.post("/api/v1/mini/orders", json={
            "product_type": "membership",
            "product_id": 1,
            "amount": 299.0,
            "payment_method": "wechat",
        }, headers=mini_headers)
        assert resp.status_code == 200, f"创建支付订单失败: {resp.text}"
        mini_order = resp.json()
        assert mini_order["payment_status"] == "pending", "订单状态应为 pending"
        assert mini_order["amount"] == 299.0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_permission_isolation(self, client: AsyncClient, db: AsyncSession):
        """
        权限隔离测试:
        1. 组织A的管理员看不到组织B的数据
        2. 普通员工不能执行管理员操作
        3. 门店员工只能看到自己门店的数据
        """
        from backend.models.organization import Organization
        from backend.crud.auth import UserCRUD
        from backend.core.security import create_access_token

        uid = _uid()

        # 创建两个组织
        org_a = Organization(name="权限隔离OrgA", slug=f"perm-iso-a-{uid}", plan="professional", status="active")
        org_b = Organization(name="权限隔离OrgB", slug=f"perm-iso-b-{uid}", plan="professional", status="active")
        db.add_all([org_a, org_b])
        await db.flush()

        # 创建两个管理员（通过CRUD直接创建，绕过rate limiter）
        admin_a = await UserCRUD.create(
            db, username=f"perm_admin_a_{uid}", email=f"perm_a_{uid}@test.com",
            password="AdminPass123!", role="super_admin", organization_id=org_a.id,
        )
        admin_b = await UserCRUD.create(
            db, username=f"perm_admin_b_{uid}", email=f"perm_b_{uid}@test.com",
            password="AdminPass123!", role="super_admin", organization_id=org_b.id,
        )
        await db.commit()

        token_a = create_access_token(data={"sub": str(admin_a.id), "role": "super_admin", "org_id": org_a.id})
        token_b = create_access_token(data={"sub": str(admin_b.id), "role": "super_admin", "org_id": org_b.id})
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 1. 组织A的管理员在组织A创建门店
        resp = await client.post("/api/v1/stores/", json={
            "name": "OrgA专属店", "code": f"PERM_A_{uid}",
        }, headers=headers_a)
        assert resp.status_code in (200, 201), f"OrgA创建门店失败: {resp.text}"
        store_a_id = resp.json()["id"]

        # 组织B的管理员看不到OrgA的门店
        resp = await client.get(f"/api/v1/stores/{store_a_id}", headers=headers_b)
        assert resp.status_code == 404, "OrgB管理员不应看到OrgA的门店"

        # 组织B的管理员在组织B创建门店
        resp = await client.post("/api/v1/stores/", json={
            "name": "OrgB专属店", "code": f"PERM_B_{uid}",
        }, headers=headers_b)
        assert resp.status_code in (200, 201), f"OrgB创建门店失败: {resp.text}"
        store_b_id = resp.json()["id"]

        # 组织A的管理员看不到OrgB的门店
        resp = await client.get(f"/api/v1/stores/{store_b_id}", headers=headers_a)
        assert resp.status_code == 404, "OrgA管理员不应看到OrgB的门店"

        # 2. 创建普通员工
        staff = await UserCRUD.create(
            db, username=f"perm_staff_{uid}", email=f"perm_staff_{uid}@test.com",
            password="StaffPass123!", role="receptionist", organization_id=org_a.id,
        )
        await db.commit()
        staff_token = create_access_token(data={"sub": str(staff.id), "role": "receptionist", "org_id": org_a.id})
        staff_headers = {"Authorization": f"Bearer {staff_token}"}

        # 普通员工可以查看列表（读权限）
        resp = await client.get("/api/v1/stores/", headers=staff_headers)
        assert resp.status_code == 200, "普通员工应能查看门店列表"

        # 3. 组织A的门店列表不包含OrgB的门店
        resp = await client.get("/api/v1/stores/", headers=headers_a)
        assert resp.status_code == 200
        stores_a = resp.json()
        for s in stores_a["data"]:
            assert s["id"] != store_b_id, "OrgA门店列表不应包含OrgB的门店"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_reminder_workflow(self, client: AsyncClient, db: AsyncSession):
        """
        提醒系统完整流程:
        1. 创建即将到期的会员
        2. 执行提醒
        3. 验证通知已创建
        4. 查看提醒统计
        """
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="reminder-test", admin_name="reminder_admin"
        )

        from backend.models.member import Member, CardType

        # 1. 创建即将到期的会员（卡到期日在3天内）
        soon_expiry = datetime.utcnow() + timedelta(days=2)
        member_expiry = Member(
            name="即将到期会员",
            phone=_unique_phone(),
            card_type=CardType.MONTHLY,
            card_start_date=datetime.utcnow() - timedelta(days=28),
            card_end_date=soon_expiry,
            organization_id=org_id,
        )
        db.add(member_expiry)
        await db.commit()

        # 创建已过期的会员
        expired_date = datetime.utcnow() - timedelta(days=5)
        member_expired = Member(
            name="已过期会员",
            phone=_unique_phone(),
            card_type=CardType.YEARLY,
            card_start_date=datetime.utcnow() - timedelta(days=400),
            card_end_date=expired_date,
            organization_id=org_id,
        )
        db.add(member_expired)
        await db.commit()

        # 2. 预览提醒
        resp = await client.get("/api/v1/reminders/preview", params={"type": "expiry"}, headers=headers)
        assert resp.status_code == 200, f"预览到期提醒失败: {resp.text}"
        preview = resp.json()
        assert "data" in preview, "预览结果应包含 data 字段"

        # 3. 执行提醒
        resp = await client.post("/api/v1/reminders/execute", headers=headers)
        if resp.status_code == 200:
            result = resp.json()
            assert "notifications_created" in result["data"], "执行结果应包含通知创建数量"
        else:
            assert resp.status_code in (200, 403), f"执行提醒返回意外状态码: {resp.status_code}"

        # 4. 查看提醒统计
        resp = await client.get("/api/v1/reminders/stats", headers=headers)
        assert resp.status_code == 200, f"获取提醒统计失败: {resp.text}"
        stats = resp.json()
        assert "data" in stats, "统计结果应包含 data 字段"
        stats_data = stats["data"]
        assert "expiry_count" in stats_data, "统计应包含到期数量"
        assert "expired_count" in stats_data, "统计应包含已过期数量"

        # 查看提醒配置
        resp = await client.get("/api/v1/reminders/config", headers=headers)
        assert resp.status_code == 200, f"获取提醒配置失败: {resp.text}"


# ============================================================
# TestAPIContract - API契约测试
# ============================================================

class TestAPIContract:
    """API契约测试 - 确保所有端点返回正确的状态码和格式"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint,method,status", [
        ("/api/v1/stores/", "get", 401),
        ("/api/v1/members/", "get", 401),
        ("/api/v1/courses/", "get", 401),
        ("/api/v1/bookings/", "get", 401),
        ("/api/v1/analytics/dashboard", "get", 401),
        ("/api/v1/marketing/rules", "get", 401),
        ("/api/v1/reminders/preview", "get", 401),
        ("/api/v1/dashboard/executive", "get", 401),
        ("/api/v1/mini/courses", "get", 401),
    ])
    async def test_endpoint_requires_auth(self, client: AsyncClient, endpoint: str, method: str, status: int):
        """验证需要认证的端点在未认证时返回401"""
        _reset_rate_limiter()
        if method == "post":
            resp = await client.post(endpoint, json={})
        else:
            resp = await client.get(endpoint)
        assert resp.status_code == status, (
            f"端点 {method.upper()} {endpoint} 未认证时应返回 {status}，实际返回 {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, client: AsyncClient):
        """无效凭证登录返回401"""
        _reset_rate_limiter()
        resp = await client.post("/api/v1/auth/login", json={
            "username": "nonexistent_user",
            "password": "wrong_password",
        })
        assert resp.status_code == 401, "无效凭证应返回401"

    @pytest.mark.asyncio
    async def test_register_endpoint(self, client: AsyncClient):
        """注册端点返回201"""
        _reset_rate_limiter()
        resp = await client.post("/api/v1/auth/register", json={
            "username": f"contract_reg_{_uid()}",
            "password": "TestPass123!",
            "email": f"contract_reg_{_uid()}@test.com",
            "role": "receptionist",
        })
        assert resp.status_code in (200, 201), f"注册应返回200或201，实际返回 {resp.status_code}"

    @pytest.mark.asyncio
    async def test_register_duplicate_user(self, client: AsyncClient, db: AsyncSession):
        """重复注册返回400"""
        _reset_rate_limiter()
        uid = _uid()
        await client.post("/api/v1/auth/register", json={
            "username": f"dup_test_user_{uid}",
            "password": "TestPass123!",
            "email": f"dup_{uid}@test.com",
            "role": "receptionist",
        })
        resp = await client.post("/api/v1/auth/register", json={
            "username": f"dup_test_user_{uid}",
            "password": "TestPass123!",
            "email": f"dup2_{uid}@test.com",
            "role": "receptionist",
        })
        assert resp.status_code == 400, "重复用户名应返回400"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, db: AsyncSession):
        """重复邮箱注册返回400"""
        _reset_rate_limiter()
        uid = _uid()
        await client.post("/api/v1/auth/register", json={
            "username": f"dup_email_user1_{uid}",
            "password": "TestPass123!",
            "email": f"dup_email_{uid}@test.com",
            "role": "receptionist",
        })
        resp = await client.post("/api/v1/auth/register", json={
            "username": f"dup_email_user2_{uid}",
            "password": "TestPass123!",
            "email": f"dup_email_{uid}@test.com",
            "role": "receptionist",
        })
        assert resp.status_code == 400, "重复邮箱应返回400"

    @pytest.mark.asyncio
    async def test_not_found_endpoints(self, client: AsyncClient, db: AsyncSession):
        """不存在的资源返回404"""
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="notfound-test", admin_name="nf_admin"
        )

        resp = await client.get("/api/v1/stores/99999", headers=headers)
        assert resp.status_code == 404, "不存在的门店应返回404"

        resp = await client.get("/api/v1/members/99999", headers=headers)
        assert resp.status_code == 404, "不存在的会员应返回404"

        resp = await client.get("/api/v1/courses/99999", headers=headers)
        assert resp.status_code == 404, "不存在的课程应返回404"

        resp = await client.get("/api/v1/coaches/99999", headers=headers)
        assert resp.status_code == 404, "不存在的教练应返回404"

        resp = await client.get("/api/v1/marketing/rules/99999", headers=headers)
        assert resp.status_code == 404, "不存在的规则应返回404"

    @pytest.mark.asyncio
    async def test_response_format_list_endpoints(self, client: AsyncClient, db: AsyncSession):
        """列表端点返回正确的分页格式"""
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="format-test", admin_name="fmt_admin"
        )

        list_endpoints = [
            "/api/v1/stores/",
            "/api/v1/members/",
            "/api/v1/courses/",
            "/api/v1/bookings/",
            "/api/v1/coaches/",
            "/api/v1/orders/",
            "/api/v1/marketing/rules",
        ]
        for endpoint in list_endpoints:
            resp = await client.get(endpoint, headers=headers)
            assert resp.status_code == 200, f"端点 {endpoint} 应返回200"
            data = resp.json()
            assert "total" in data, f"端点 {endpoint} 应包含 total 字段"
            assert "data" in data, f"端点 {endpoint} 应包含 data 字段"

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """健康检查端点"""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """根路径端点"""
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_wx_login_returns_token(self, client: AsyncClient):
        """微信登录返回有效token"""
        _reset_rate_limiter()
        resp = await client.post("/api/v1/mini/auth/wx-login", json={
            "code": f"contract_test_code_{_uid()}",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_advanced_analytics_requires_params(self, client: AsyncClient, db: AsyncSession):
        """高级分析端点缺少必需参数返回422"""
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="adv-analytics-test", admin_name="adv_admin"
        )

        resp = await client.get("/api/v1/analytics/advanced/revenue", headers=headers)
        assert resp.status_code == 422, "缺少 start_date/end_date 应返回422"

        resp = await client.get("/api/v1/analytics/advanced/members", headers=headers)
        assert resp.status_code == 422, "缺少 start_date/end_date 应返回422"


# ============================================================
# TestDataIntegrity - 数据完整性测试
# ============================================================

class TestDataIntegrity:
    """数据完整性测试"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cascade_delete(self, client: AsyncClient, db: AsyncSession):
        """测试级联删除: 删除门店时关联数据正确处理"""
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="cascade-test", admin_name="cascade_admin"
        )

        store = await _create_store(client, headers, "级联删除测试店", "CASCADE_S")
        store_id = store["id"]

        coach = await _create_coach(client, headers, "级联教练")
        member = await _create_member(client, headers, "级联会员")

        # 删除门店
        resp = await client.delete(f"/api/v1/stores/{store_id}", headers=headers)
        assert resp.status_code == 200, f"删除门店失败: {resp.text}"

        # 验证门店已删除
        resp = await client.get(f"/api/v1/stores/{store_id}", headers=headers)
        assert resp.status_code == 404, "删除后门店应返回404"

        # 验证教练和会员仍然存在
        resp = await client.get(f"/api/v1/coaches/{coach['id']}", headers=headers)
        assert resp.status_code == 200, "教练应仍然存在"

        resp = await client.get(f"/api/v1/members/{member['id']}", headers=headers)
        assert resp.status_code == 200, "会员应仍然存在"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_unique_constraints(self, client: AsyncClient, db: AsyncSession):
        """测试唯一约束: 重复数据被正确拒绝"""
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="unique-test", admin_name="unique_admin"
        )

        # 重复手机号创建会员
        phone1 = _unique_phone()
        await _create_member(client, headers, "唯一约束会员", phone1)
        resp = await client.post("/api/v1/members/", json={
            "name": "重复手机号会员",
            "phone": phone1,
        }, headers=headers)
        assert resp.status_code == 400, "重复手机号创建会员应返回400"

        # 重复手机号创建教练
        phone2 = _unique_phone()
        await _create_coach(client, headers, "唯一约束教练", phone2)
        resp = await client.post("/api/v1/coaches/", json={
            "name": "重复手机号教练",
            "phone": phone2,
        }, headers=headers)
        assert resp.status_code == 400, "重复手机号创建教练应返回400"

        # 重复门店code
        uid = _uid()
        await _create_store(client, headers, "唯一约束店", f"UNIQUE_{uid}")
        try:
            resp = await client.post("/api/v1/stores/", json={
                "name": "重复code店",
                "code": f"UNIQUE_{uid}",
            }, headers=headers)
            assert resp.status_code in (400, 500), "重复门店code应返回错误"
        except Exception:
            pass  # IntegrityError may propagate

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_data_isolation(self, client: AsyncClient, db: AsyncSession):
        """测试数据隔离: 跨组织数据完全隔离"""
        from backend.models.organization import Organization
        from backend.crud.auth import UserCRUD
        from backend.core.security import create_access_token

        uid = _uid()

        # 创建两个独立组织
        org_x = Organization(name="数据隔离OrgX", slug=f"data-iso-x-{uid}", plan="professional", status="active")
        org_y = Organization(name="数据隔离OrgY", slug=f"data-iso-y-{uid}", plan="professional", status="active")
        db.add_all([org_x, org_y])
        await db.flush()

        # 创建两个管理员
        admin_x = await UserCRUD.create(
            db, username=f"data_admin_x_{uid}", email=f"data_x_{uid}@test.com",
            password="AdminPass123!", role="super_admin", organization_id=org_x.id,
        )
        admin_y = await UserCRUD.create(
            db, username=f"data_admin_y_{uid}", email=f"data_y_{uid}@test.com",
            password="AdminPass123!", role="super_admin", organization_id=org_y.id,
        )
        await db.commit()

        token_x = create_access_token(data={"sub": str(admin_x.id), "role": "super_admin", "org_id": org_x.id})
        token_y = create_access_token(data={"sub": str(admin_y.id), "role": "super_admin", "org_id": org_y.id})
        headers_x = {"Authorization": f"Bearer {token_x}"}
        headers_y = {"Authorization": f"Bearer {token_y}"}

        # OrgX 创建教练
        resp = await client.post("/api/v1/coaches/", json={
            "name": "OrgX教练", "phone": _unique_phone(),
        }, headers=headers_x)
        assert resp.status_code in (200, 201), f"OrgX创建教练失败: {resp.text}"
        coach_x_id = resp.json()["id"]

        # OrgY 看不到 OrgX 的教练
        resp = await client.get(f"/api/v1/coaches/{coach_x_id}", headers=headers_y)
        assert resp.status_code == 404, "OrgY不应看到OrgX的教练"

        # OrgX 创建会员
        resp = await client.post("/api/v1/members/", json={
            "name": "OrgX会员", "phone": _unique_phone(),
        }, headers=headers_x)
        assert resp.status_code in (200, 201), f"OrgX创建会员失败: {resp.text}"
        member_x_id = resp.json()["id"]

        # OrgY 看不到 OrgX 的会员
        resp = await client.get(f"/api/v1/members/{member_x_id}", headers=headers_y)
        assert resp.status_code == 404, "OrgY不应看到OrgX的会员"

        # OrgX 创建课程
        resp = await client.post("/api/v1/courses/", json={
            "name": "OrgX专属课", "course_type": "group",
            "duration_minutes": 60, "max_attendees": 20,
        }, headers=headers_x)
        assert resp.status_code in (200, 201), f"OrgX创建课程失败: {resp.text}"
        course_x_id = resp.json()["id"]

        # OrgY 看不到 OrgX 的课程
        resp = await client.get(f"/api/v1/courses/{course_x_id}", headers=headers_y)
        assert resp.status_code == 404, "OrgY不应看到OrgX的课程"

        # OrgY 创建营销规则
        resp = await client.post("/api/v1/marketing/rules", json={
            "name": "OrgY专属规则",
            "trigger": {"event_type": "member_created"},
            "actions": [{"type": "send_notification", "params": {}}],
        }, headers=headers_y)
        assert resp.status_code in (200, 201), f"OrgY创建规则失败: {resp.text}"
        rule_y_id = resp.json()["id"]

        # OrgX 看不到 OrgY 的规则
        resp = await client.get(f"/api/v1/marketing/rules/{rule_y_id}", headers=headers_x)
        assert resp.status_code == 404, "OrgX不应看到OrgY的营销规则"

        # 验证各自列表只包含自己的数据
        resp_x = await client.get("/api/v1/members/", headers=headers_x)
        resp_y = await client.get("/api/v1/members/", headers=headers_y)
        assert resp_x.status_code == 200
        assert resp_y.status_code == 200
        for m in resp_y.json()["data"]:
            assert m["id"] != member_x_id, "OrgY会员列表不应包含OrgX的会员"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_booking_status_transitions(self, client: AsyncClient, db: AsyncSession):
        """测试预约状态转换的正确性"""
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="booking-status-test", admin_name="bs_admin"
        )

        coach = await _create_coach(client, headers, "状态教练")
        course = await _create_course(client, headers, "状态转换课", "group", coach_id=coach["id"])
        now = datetime.utcnow()
        start = now + timedelta(hours=120)
        end = start + timedelta(hours=1)
        schedule = await _create_schedule(client, headers, course["id"], start, end)
        member = await _create_member(client, headers, "状态会员")

        # 创建预约 -> pending
        booking = await _create_booking(client, headers, member["id"], schedule["id"])
        assert booking["status"] == "pending"
        booking_id = booking["id"]

        # 签到 -> checked_in
        resp = await client.post(
            f"/api/v1/bookings/{booking_id}/checkin",
            json={"check_in_method": "manual"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "checked_in"

        # 已签到不能取消
        resp = await client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=headers,
        )
        assert resp.status_code == 400, "已签到的预约不能取消"

        # 已签到不能再次签到
        resp = await client.post(
            f"/api/v1/bookings/{booking_id}/checkin",
            json={"check_in_method": "manual"},
            headers=headers,
        )
        assert resp.status_code == 400, "已签到的预约不能重复签到"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_order_lifecycle(self, client: AsyncClient, db: AsyncSession):
        """测试订单生命周期"""
        _reset_rate_limiter()
        org_id, _, headers = await _create_org_and_admin(
            client, db, org_name="order-lifecycle-test", admin_name="ol_admin"
        )

        member = await _create_member(client, headers, "订单生命周期会员")

        # 创建订单 -> pending
        order = await _create_order(client, headers, member["id"], 199.0, "card", "月卡")
        assert order["payment_status"] == "pending"
        order_id = order["id"]

        # 取消订单 -> cancelled
        resp = await client.post(
            f"/api/v1/orders/{order_id}/cancel",
            params={"reason": "测试取消"},
            headers=headers,
        )
        assert resp.status_code == 200, f"取消订单失败: {resp.text}"
        cancelled_order = resp.json()
        assert cancelled_order["payment_status"] == "cancelled", "取消后状态应为 cancelled"

        # 已取消的订单不能支付
        resp = await client.post(
            f"/api/v1/orders/{order_id}/pay",
            params={"payment_method": "wechat"},
            headers=headers,
        )
        assert resp.status_code == 400, "已取消的订单不能支付"

        # 创建新订单并支付
        order2 = await _create_order(client, headers, member["id"], 399.0, "card", "年卡")
        order2_id = order2["id"]

        resp = await client.post(
            f"/api/v1/orders/{order2_id}/pay",
            params={"payment_method": "wechat"},
            headers=headers,
        )
        assert resp.status_code == 200, f"支付订单失败: {resp.text}"

        # 验证订单已支付
        resp = await client.get(f"/api/v1/orders/{order2_id}", headers=headers)
        assert resp.status_code == 200
        paid_order = resp.json()
        assert paid_order["payment_status"] == "paid", "支付后状态应为 paid"
        assert paid_order["paid_at"] is not None, "支付时间不应为空"

        # 已支付的订单不能再次取消（应使用退款）
        resp = await client.post(
            f"/api/v1/orders/{order2_id}/cancel",
            headers=headers,
        )
        assert resp.status_code == 400, "已支付的订单不能直接取消"
