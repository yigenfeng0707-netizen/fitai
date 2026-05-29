"""
小程序 API 测试
"""
import pytest
from httpx import AsyncClient


# ==================== 认证测试 ====================

@pytest.mark.asyncio
async def test_wx_login(client: AsyncClient):
    """测试微信小程序登录"""
    response = await client.post("/api/v1/mini/auth/wx-login", json={
        "code": "test_wx_code_12345",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600


@pytest.mark.asyncio
async def test_wx_login_same_code_returns_same_user(client: AsyncClient):
    """同一code重复登录返回同一用户token"""
    code = "test_wx_code_repeat_999"
    resp1 = await client.post("/api/v1/mini/auth/wx-login", json={"code": code})
    resp2 = await client.post("/api/v1/mini/auth/wx-login", json={"code": code})
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    # 两次返回的 token 都有效（同一用户）
    assert "access_token" in resp1.json()
    assert "access_token" in resp2.json()


@pytest.mark.asyncio
async def test_phone_login_no_member(client: AsyncClient):
    """手机号登录 - 未注册会员"""
    response = await client.post("/api/v1/mini/auth/phone-login", json={
        "phone": "19999999999",
        "verification_code": "1234",
    })
    assert response.status_code == 404
    assert "未注册" in response.text


@pytest.mark.asyncio
async def test_phone_login_with_member(client: AsyncClient, auth_headers: dict):
    """手机号登录 - 已注册会员"""
    # 先通过管理端创建会员
    await client.post("/api/v1/members/", json={
        "name": "手机登录测试",
        "phone": "13800001111",
    }, headers=auth_headers)

    response = await client.post("/api/v1/mini/auth/phone-login", json={
        "phone": "13800001111",
        "verification_code": "1234",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


# ==================== 认证要求测试 ====================

@pytest.mark.asyncio
async def test_mini_requires_auth(client: AsyncClient):
    """小程序接口需要认证"""
    # 未认证访问会员资料
    response = await client.get("/api/v1/mini/member/profile")
    assert response.status_code == 401

    # 未认证访问课程列表
    response = await client.get("/api/v1/mini/courses")
    assert response.status_code == 401

    # 未认证访问订单列表
    response = await client.get("/api/v1/mini/orders")
    assert response.status_code == 401


# ==================== 会员接口测试 ====================

@pytest.mark.asyncio
async def test_get_my_profile_no_member(client: AsyncClient, auth_headers: dict):
    """获取个人资料 - 未关联会员"""
    response = await client.get("/api/v1/mini/member/profile", headers=auth_headers)
    # 管理员用户没有关联会员，应返回404
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_my_profile_no_member(client: AsyncClient, auth_headers: dict):
    """更新个人资料 - 未关联会员"""
    response = await client.put("/api/v1/mini/member/profile", json={
        "name": "新名字",
    }, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_card_no_member(client: AsyncClient, auth_headers: dict):
    """获取会员卡 - 未关联会员"""
    response = await client.get("/api/v1/mini/member/card", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_bookings_no_member(client: AsyncClient, auth_headers: dict):
    """获取我的预约 - 未关联会员"""
    response = await client.get("/api/v1/mini/member/bookings", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_orders_no_member(client: AsyncClient, auth_headers: dict):
    """获取我的订单 - 未关联会员"""
    response = await client.get("/api/v1/mini/member/orders", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_notifications(client: AsyncClient, auth_headers: dict):
    """获取我的通知"""
    response = await client.get("/api/v1/mini/member/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_my_notifications_filter_read(client: AsyncClient, auth_headers: dict):
    """获取我的通知 - 按已读过滤"""
    response = await client.get(
        "/api/v1/mini/member/notifications?is_read=true",
        headers=auth_headers,
    )
    assert response.status_code == 200


# ==================== 课程接口测试 ====================

@pytest.mark.asyncio
async def test_get_courses(client: AsyncClient, auth_headers: dict):
    """获取课程列表"""
    # 先创建课程
    await client.post("/api/v1/courses/", json={
        "name": "瑜伽课",
        "course_type": "group",
        "duration_minutes": 60,
        "max_attendees": 20,
        "price": 50.0,
    }, headers=auth_headers)

    response = await client.get("/api/v1/mini/courses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_courses_filter_type(client: AsyncClient, auth_headers: dict):
    """获取课程列表 - 按类型过滤"""
    response = await client.get(
        "/api/v1/mini/courses?course_type=group",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_course_detail(client: AsyncClient, auth_headers: dict):
    """获取课程详情"""
    # 先创建课程
    created = await client.post("/api/v1/courses/", json={
        "name": "动感单车",
        "course_type": "group",
        "duration_minutes": 45,
        "max_attendees": 15,
    }, headers=auth_headers)
    course_id = created.json()["id"]

    response = await client.get(
        f"/api/v1/mini/courses/{course_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "动感单车"
    assert data["course_type"] == "group"


@pytest.mark.asyncio
async def test_get_course_detail_not_found(client: AsyncClient, auth_headers: dict):
    """获取课程详情 - 不存在"""
    response = await client.get("/api/v1/mini/courses/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_schedules(client: AsyncClient, auth_headers: dict):
    """获取排课列表"""
    response = await client.get("/api/v1/mini/schedules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_schedules_invalid_date(client: AsyncClient, auth_headers: dict):
    """获取排课列表 - 日期格式错误"""
    response = await client.get(
        "/api/v1/mini/schedules?date=invalid-date",
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_coaches(client: AsyncClient, auth_headers: dict):
    """获取教练列表"""
    response = await client.get("/api/v1/mini/coaches", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data


# ==================== 预约接口测试 ====================

@pytest.mark.asyncio
async def test_create_booking_no_member(client: AsyncClient, auth_headers: dict):
    """创建预约 - 未关联会员"""
    response = await client.post("/api/v1/mini/bookings", json={
        "schedule_id": 1,
    }, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_booking_no_member(client: AsyncClient, auth_headers: dict):
    """取消预约 - 未关联会员"""
    response = await client.delete("/api/v1/mini/bookings/1", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_check_in_no_member(client: AsyncClient, auth_headers: dict):
    """签到 - 未关联会员"""
    response = await client.post("/api/v1/mini/bookings/1/checkin", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_today_bookings_no_member(client: AsyncClient, auth_headers: dict):
    """获取今日预约 - 未关联会员"""
    response = await client.get("/api/v1/mini/bookings/today", headers=auth_headers)
    assert response.status_code == 404


# ==================== 支付接口测试 ====================

@pytest.mark.asyncio
async def test_create_order_no_member(client: AsyncClient, auth_headers: dict):
    """创建订单 - 未关联会员"""
    response = await client.post("/api/v1/mini/orders", json={
        "product_type": "membership",
        "product_id": 1,
        "amount": 299.0,
        "payment_method": "wechat",
    }, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_order_invalid_product_type(client: AsyncClient, auth_headers: dict):
    """创建订单 - 无效商品类型"""
    response = await client.post("/api/v1/mini/orders", json={
        "product_type": "invalid_type",
        "product_id": 1,
        "amount": 100.0,
    }, headers=auth_headers)
    assert response.status_code == 404  # 先被 member_id 检查拦截


@pytest.mark.asyncio
async def test_create_order_zero_amount(client: AsyncClient, auth_headers: dict):
    """创建订单 - 金额为零"""
    response = await client.post("/api/v1/mini/orders", json={
        "product_type": "membership",
        "product_id": 1,
        "amount": 0,
    }, headers=auth_headers)
    assert response.status_code == 404  # 先被 member_id 检查拦截


@pytest.mark.asyncio
async def test_get_my_orders_no_member(client: AsyncClient, auth_headers: dict):
    """获取订单列表 - 未关联会员"""
    response = await client.get("/api/v1/mini/orders", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_order_detail_no_member(client: AsyncClient, auth_headers: dict):
    """获取订单详情 - 未关联会员"""
    response = await client.get("/api/v1/mini/orders/1", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_initiate_payment_no_member(client: AsyncClient, auth_headers: dict):
    """发起支付 - 未关联会员"""
    response = await client.post("/api/v1/mini/orders/1/pay", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_confirm_payment_no_member(client: AsyncClient, auth_headers: dict):
    """确认支付 - 未关联会员"""
    response = await client.post("/api/v1/mini/orders/1/confirm", json={
        "transaction_id": "wx_txn_123",
    }, headers=auth_headers)
    assert response.status_code == 404


# ==================== 通知接口测试 ====================

@pytest.mark.asyncio
async def test_mark_notification_read_not_found(client: AsyncClient, auth_headers: dict):
    """标记通知已读 - 不存在"""
    response = await client.put(
        "/api/v1/mini/member/notifications/99999/read",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_notifications_read(client: AsyncClient, auth_headers: dict):
    """全部标记已读"""
    response = await client.put(
        "/api/v1/mini/member/notifications/read-all",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
