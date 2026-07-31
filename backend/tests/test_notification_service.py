"""
通知推送服务测试 - 多渠道分发、批量发送、模板 CRUD
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.notification_service import (
    NotificationDispatcher,
    InAppChannel,
    SMSChannel,
    WeChatWorkChannel,
    setup_notification_channels,
)
from backend.models.notification import Notification, NotificationType


class TestNotificationDispatcher:
    """通知分发器单元测试"""

    def test_register_channel(self):
        """测试注册渠道"""
        dispatcher = NotificationDispatcher()
        channel = InAppChannel()
        dispatcher.register_channel("in_app", channel)
        assert "in_app" in dispatcher.get_registered_channels()

    def test_register_multiple_channels(self):
        """测试注册多个渠道"""
        dispatcher = setup_notification_channels()
        channels = dispatcher.get_registered_channels()
        assert "in_app" in channels
        assert "sms" in channels
        assert "wechat_work" in channels

    def test_unregister_channel(self):
        """测试取消注册渠道"""
        dispatcher = NotificationDispatcher()
        dispatcher.register_channel("in_app", InAppChannel())
        dispatcher.unregister_channel("in_app")
        assert "in_app" not in dispatcher.get_registered_channels()

    @pytest.mark.asyncio
    async def test_send_unregistered_channel(self):
        """测试发送到未注册的渠道"""
        dispatcher = NotificationDispatcher()
        result = await dispatcher.send(
            channels=["nonexistent"],
            user_id=1,
            title="测试",
            content="测试内容",
        )
        assert result["success"] is False
        assert "nonexistent" in result["results"]
        assert result["results"]["nonexistent"] is False
        assert any("not registered" in e for e in result["errors"])


class TestInAppChannel:
    """站内通知渠道测试"""

    @pytest.mark.asyncio
    async def test_send_creates_notification(self, db):
        """测试站内通知创建数据库记录"""
        channel = InAppChannel()
        success = await channel.send(
            user_id=1,
            title="测试标题",
            content="测试内容",
            link="/test",
            extra_data={"key": "value"},
            db=db,
            organization_id=1,
            notification_type=NotificationType.SYSTEM,
        )
        assert success is True

        from sqlalchemy import select
        result = await db.execute(select(Notification).where(Notification.user_id == 1))
        notification = result.scalar_one_or_none()
        assert notification is not None
        assert notification.title == "测试标题"
        assert notification.content == "测试内容"
        assert notification.link == "/test"
        assert notification.extra_data == {"key": "value"}
        assert notification.organization_id == 1

    @pytest.mark.asyncio
    async def test_send_without_db(self):
        """测试无数据库会话时返回 False"""
        channel = InAppChannel()
        success = await channel.send(
            user_id=1,
            title="测试标题",
            content="测试内容",
            db=None,
        )
        assert success is False


class TestSMSChannel:
    """短信通知渠道测试"""

    @pytest.mark.asyncio
    async def test_send_sms_disabled(self):
        """测试 SMS 禁用时返回 False"""
        channel = SMSChannel()
        success = await channel.send(
            user_id=1,
            title="测试",
            content="测试内容",
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_send_sms_enabled_stub(self):
        """测试 SMS 启用时 stub 返回 True"""
        channel = SMSChannel()
        with patch("backend.services.notification_service.settings") as mock_settings:
            mock_settings.SMS_ENABLED = True
            mock_settings.SMS_ACCESS_KEY = "test_key"
            mock_settings.SMS_ACCESS_SECRET = "test_secret"
            mock_settings.SMS_SIGN_NAME = "test_sign"
            mock_settings.SMS_TEMPLATE_CODE = "SMS_123456"
            # Mock httpx to prevent real API call
            with patch("backend.services.notification_service.httpx") as mock_httpx:
                mock_response = MagicMock()
                mock_response.json.return_value = {"Code": "OK"}
                mock_httpx.AsyncClient.return_value.__aenter__.return_value.get.return_value = mock_response
                success = await channel.send(
                    user_id=1,
                    title="验证码",
                    content="您的验证码是 123456",
                    phone="13800138000",
                )
                assert success is True


class TestWeChatWorkChannel:
    """企业微信通知渠道测试"""

    @pytest.mark.asyncio
    async def test_send_wechat_work_disabled(self):
        """测试企业微信禁用时返回 False"""
        channel = WeChatWorkChannel()
        success = await channel.send(
            user_id=1,
            title="测试",
            content="测试内容",
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_send_wechat_work_enabled_stub(self):
        """测试企业微信启用时 stub 返回 True"""
        channel = WeChatWorkChannel()
        with patch("backend.services.notification_service.settings") as mock_settings:
            mock_settings.WECHAT_WORK_ENABLED = True
            mock_settings.WECHAT_WORK_CORP_ID = "test_corp"
            mock_settings.WECHAT_WORK_AGENT_ID = "test_agent"
            mock_settings.WECHAT_WORK_SECRET = "test_secret"
            # Mock httpx to prevent real API call
            with patch("backend.services.notification_service.httpx") as mock_httpx:
                mock_response = MagicMock()
                mock_response.json.return_value = {"errcode": 0}
                mock_httpx.AsyncClient.return_value.__aenter__.return_value.post.return_value = mock_response
                success = await channel.send(
                    user_id=1,
                    title="会议提醒",
                    content="明天10点团队会议",
                )
                assert success is True


class TestNotificationServiceAPI:
    """通知推送 API 集成测试"""

    @pytest.mark.asyncio
    async def test_send_in_app_notification(self, client, db, auth_headers):
        """测试通过 API 发送站内通知"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        resp = await client.post("/api/v1/notifications/send", json={
            "user_id": user_id,
            "title": "多渠道测试",
            "content": "这是一条站内通知",
            "channels": ["in_app"],
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["channel_results"]["in_app"] is True
        assert data["errors"] == []

        # 验证数据库中确实创建了通知
        resp = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert any(n["title"] == "多渠道测试" for n in resp.json()["data"])

    @pytest.mark.asyncio
    async def test_send_multi_channel_notification(self, client, db, auth_headers):
        """测试通过 API 多渠道发送通知"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        resp = await client.post("/api/v1/notifications/send", json={
            "user_id": user_id,
            "title": "多渠道通知",
            "content": "同时发送到站内和短信",
            "channels": ["in_app", "sms"],
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # in_app 应该成功，sms 禁用应该失败
        assert data["channel_results"]["in_app"] is True
        assert data["channel_results"]["sms"] is False
        # 整体 success 应为 False（sms 失败）
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_send_batch_notification(self, client, db, auth_headers):
        """测试通过 API 批量发送通知"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        resp = await client.post("/api/v1/notifications/send/batch", json={
            "user_ids": [user_id],
            "title": "批量通知",
            "content": "批量发送测试",
            "channels": ["in_app"],
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["total"] == 1
        assert data["success_count"] == 1

    @pytest.mark.asyncio
    async def test_send_notification_requires_auth(self, client):
        """测试发送通知需要认证"""
        resp = await client.post("/api/v1/notifications/send", json={
            "user_id": 1,
            "title": "测试",
            "content": "未认证",
            "channels": ["in_app"],
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_send_batch_requires_auth(self, client):
        """测试批量发送需要认证"""
        resp = await client.post("/api/v1/notifications/send/batch", json={
            "user_ids": [1, 2],
            "title": "测试",
            "content": "未认证",
            "channels": ["in_app"],
        })
        assert resp.status_code == 401


class TestNotificationTemplateCRUD:
    """通知模板 CRUD 测试"""

    @pytest.mark.asyncio
    async def test_create_notification_template(self, client, auth_headers):
        """测试创建通知模板"""
        resp = await client.post("/api/v1/notifications/templates", json={
            "name": "会员到期提醒",
            "code": "member_expiry",
            "title_template": "您的会员卡即将到期",
            "content_template": "您的{card_name}将于{expiry_date}到期，请及时续费。",
            "channels": ["in_app", "sms"],
            "notification_type": "card_expiring",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "会员到期提醒"
        assert data["code"] == "member_expiry"
        assert data["channels"] == ["in_app", "sms"]
        assert data["id"] > 0

    @pytest.mark.asyncio
    async def test_create_duplicate_template_code(self, client, auth_headers):
        """测试重复模板 code 返回错误"""
        template_data = {
            "name": "重复模板",
            "code": "duplicate_code",
            "title_template": "测试标题",
            "content_template": "测试内容",
        }
        resp = await client.post("/api/v1/notifications/templates", json=template_data, headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.post("/api/v1/notifications/templates", json=template_data, headers=auth_headers)
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_notification_templates(self, client, auth_headers):
        """测试获取通知模板列表"""
        # 先创建一个模板
        await client.post("/api/v1/notifications/templates", json={
            "name": "课程提醒",
            "code": "class_reminder_tpl",
            "title_template": "课程提醒",
            "content_template": "您有一节{course_name}课程即将开始",
            "channels": ["in_app"],
            "notification_type": "class_reminder",
        }, headers=auth_headers)

        resp = await client.get("/api/v1/notifications/templates", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(t["code"] == "class_reminder_tpl" for t in data["data"])

    @pytest.mark.asyncio
    async def test_templates_requires_auth(self, client):
        """测试模板接口需要认证"""
        resp = await client.get("/api/v1/notifications/templates")
        assert resp.status_code == 401

        resp = await client.post("/api/v1/notifications/templates", json={
            "name": "测试",
            "code": "test_no_auth",
            "title_template": "测试",
            "content_template": "测试",
        })
        assert resp.status_code == 401
