"""自动提醒 API 测试"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.member import Member, MemberStatus, CardType
from backend.models.booking import Booking, BookingStatus


@pytest.mark.asyncio
async def test_preview_birthday_reminders(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """预览生日提醒 - 应返回即将过生日的会员"""
    # 获取当前用户的 organization_id
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    org_id = resp.json()["organization_id"]

    # 创建一个生日在3天后的会员
    birthday = datetime.utcnow() + timedelta(days=3)
    await client.post("/api/v1/members/", json={
        "name": "寿星会员",
        "phone": "13800001111",
        "birthday": birthday.strftime("%Y-%m-%d"),
    }, headers=auth_headers)

    # 预览生日提醒
    resp = await client.get("/api/v1/reminders/preview?type=birthday", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    # 至少有一个匹配
    birthday_items = [item for item in data["data"] if item["type"] == "birthday"]
    assert len(birthday_items) >= 1
    # 验证字段
    item = birthday_items[0]
    assert "member_id" in item
    assert "member_name" in item
    assert "phone" in item
    assert item["type"] == "birthday"
    assert "days_until" in item


@pytest.mark.asyncio
async def test_preview_expiry_reminders(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """预览到期提醒 - 应返回即将到期的会员卡"""
    # 创建一个卡在15天后到期的会员
    expiry_date = datetime.utcnow() + timedelta(days=15)
    await client.post("/api/v1/members/", json={
        "name": "即将到期会员",
        "phone": "13800002222",
        "initial_card_type": "yearly",
    }, headers=auth_headers)

    # 手动设置 card_end_date 为15天后
    from sqlalchemy import select, update
    from backend.models.member import Member
    result = await db.execute(select(Member).where(Member.phone == "13800002222"))
    member = result.scalar_one_or_none()
    if member:
        member.card_end_date = expiry_date
        await db.flush()

    # 预览到期提醒
    resp = await client.get("/api/v1/reminders/preview?type=expiry", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    expiry_items = [item for item in data["data"] if item["type"] == "expiry"]
    assert len(expiry_items) >= 1
    item = expiry_items[0]
    assert item["type"] == "expiry"
    assert item["days_until"] > 0


@pytest.mark.asyncio
async def test_preview_no_visit_reminders(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """预览未到店提醒 - 应返回长时间未到店的会员"""
    # 创建一个没有预约记录的会员
    await client.post("/api/v1/members/", json={
        "name": "久未来会员",
        "phone": "13800003333",
    }, headers=auth_headers)

    # 预览未到店提醒（设置较长的天数以确保匹配）
    resp = await client.get("/api/v1/reminders/preview?type=no_visit", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    no_visit_items = [item for item in data["data"] if item["type"] == "no_visit"]
    assert len(no_visit_items) >= 1
    item = no_visit_items[0]
    assert item["type"] == "no_visit"
    assert item["days_until"] < 0


@pytest.mark.asyncio
async def test_execute_reminders(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """执行提醒 - 应创建通知"""
    # 创建一个生日在3天后的会员
    birthday = datetime.utcnow() + timedelta(days=3)
    await client.post("/api/v1/members/", json={
        "name": "执行测试会员",
        "phone": "13800004444",
        "birthday": birthday.strftime("%Y-%m-%d"),
    }, headers=auth_headers)

    # 执行提醒
    resp = await client.post("/api/v1/reminders/execute", json={
        "birthday_enabled": True,
        "expiry_enabled": False,
        "expired_enabled": False,
        "no_visit_enabled": False,
        "birthday_days_ahead": 7,
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "notifications_created" in data["data"]
    assert data["data"]["processed"]["birthday_count"] >= 1


@pytest.mark.asyncio
async def test_reminder_stats(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """获取提醒统计"""
    resp = await client.get("/api/v1/reminders/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    stats = data["data"]
    assert "birthday_count" in stats
    assert "expiry_count" in stats
    assert "expired_count" in stats
    assert "no_visit_count" in stats
    assert "total_notifications_sent" in stats
    # 所有计数应为非负整数
    assert stats["birthday_count"] >= 0
    assert stats["expiry_count"] >= 0
    assert stats["expired_count"] >= 0
    assert stats["no_visit_count"] >= 0


@pytest.mark.asyncio
async def test_reminder_config(client: AsyncClient, auth_headers: dict):
    """获取提醒配置"""
    resp = await client.get("/api/v1/reminders/config", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    config = data["data"]
    assert config["birthday_days_ahead"] == 7
    assert config["expiry_days_ahead"] == 30
    assert config["expired_days_after"] == 7
    assert config["no_visit_days"] == 30
    assert config["birthday_enabled"] is True
    assert config["expiry_enabled"] is True


@pytest.mark.asyncio
async def test_reminder_config_update(client: AsyncClient, auth_headers: dict):
    """更新提醒配置"""
    resp = await client.put("/api/v1/reminders/config", json={
        "birthday_days_ahead": 14,
        "expiry_days_ahead": 60,
        "no_visit_days": 45,
        "birthday_enabled": True,
        "expiry_enabled": True,
        "expired_enabled": False,
        "no_visit_enabled": True,
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    config = data["data"]
    assert config["birthday_days_ahead"] == 14
    assert config["expiry_days_ahead"] == 60
    assert config["expired_enabled"] is False
    assert config["no_visit_days"] == 45


@pytest.mark.asyncio
async def test_reminder_requires_admin_for_execute(client: AsyncClient, auth_headers: dict):
    """执行提醒需要 marketing:write 权限 - 当前测试用户为 super_admin，应可执行"""
    # super_admin 有 marketing:write 权限，所以应该成功
    resp = await client.post("/api/v1/reminders/execute", json={
        "birthday_enabled": False,
        "expiry_enabled": False,
        "expired_enabled": False,
        "no_visit_enabled": False,
    }, headers=auth_headers)
    assert resp.status_code == 200

    # 创建一个没有 marketing:write 权限的用户来测试
    # 先注册一个 receptionist 用户（有 marketing:write 权限）
    await client.post("/api/v1/auth/register", json={
        "username": "test_receptionist",
        "password": "Testpass123",
        "role": "receptionist",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "username": "test_receptionist",
        "password": "Testpass123",
    })
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        receptionist_headers = {"Authorization": f"Bearer {token}"}
        # receptionist 有 marketing:write，应该成功
        resp = await client.post("/api/v1/reminders/execute", json={
            "birthday_enabled": False,
            "expiry_enabled": False,
            "expired_enabled": False,
            "no_visit_enabled": False,
        }, headers=receptionist_headers)
        assert resp.status_code == 200

    # 创建一个 finance 用户（没有 marketing:write 权限）
    await client.post("/api/v1/auth/register", json={
        "username": "test_finance",
        "password": "Testpass123",
        "role": "finance",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "username": "test_finance",
        "password": "Testpass123",
    })
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        finance_headers = {"Authorization": f"Bearer {token}"}
        # finance 没有 marketing:write，应该被拒绝
        resp = await client.post("/api/v1/reminders/execute", json={
            "birthday_enabled": False,
            "expiry_enabled": False,
            "expired_enabled": False,
            "no_visit_enabled": False,
        }, headers=finance_headers)
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_preview_all_types(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """预览所有类型的提醒（不指定 type 参数）"""
    # 创建一个生日在3天后的会员
    birthday = datetime.utcnow() + timedelta(days=3)
    await client.post("/api/v1/members/", json={
        "name": "全类型测试会员",
        "phone": "13800005555",
        "birthday": birthday.strftime("%Y-%m-%d"),
    }, headers=auth_headers)

    resp = await client.get("/api/v1/reminders/preview", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    # 应返回所有类型
    types_returned = set(item["type"] for item in data["data"])
    assert "birthday" in types_returned or "expiry" in types_returned or "no_visit" in types_returned


@pytest.mark.asyncio
async def test_preview_invalid_type(client: AsyncClient, auth_headers: dict):
    """预览提醒 - 无效的 type 参数应被验证拒绝"""
    resp = await client.get("/api/v1/reminders/preview?type=invalid_type", headers=auth_headers)
    assert resp.status_code == 422
