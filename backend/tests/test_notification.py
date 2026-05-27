"""消息通知 API 测试"""
import pytest


class TestNotificationAPI:
    @pytest.mark.asyncio
    async def test_empty_notifications(self, client, auth_headers):
        """无通知时返回空列表"""
        resp = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_unread_count_empty(self, client, auth_headers):
        resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_batch_create_and_list(self, client, db, auth_headers):
        """批量创建通知并查询"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        resp = await client.post("/api/v1/notifications/batch", json={
            "user_ids": [user_id],
            "notification_type": "system",
            "title": "测试通知1",
            "content": "这是测试内容",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert "1 条" in resp.json()["message"]

        await client.post("/api/v1/notifications/batch", json={
            "user_ids": [user_id],
            "notification_type": "class_reminder",
            "title": "上课提醒",
            "content": "明天10点瑜伽课",
        }, headers=auth_headers)

        resp = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_unread_count_after_create(self, client, db, auth_headers):
        """创建后未读数增加"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        await client.post("/api/v1/notifications/batch", json={
            "user_ids": [user_id],
            "notification_type": "card_expiring",
            "title": "会员卡即将到期",
        }, headers=auth_headers)

        resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    @pytest.mark.asyncio
    async def test_mark_read(self, client, db, auth_headers):
        """标记已读"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        await client.post("/api/v1/notifications/batch", json={
            "user_ids": [user_id],
            "notification_type": "system",
            "title": "待读通知",
        }, headers=auth_headers)

        resp = await client.get("/api/v1/notifications/?is_read=false", headers=auth_headers)
        notification_id = resp.json()["data"][0]["id"]

        resp = await client.put(f"/api/v1/notifications/{notification_id}/read", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    @pytest.mark.asyncio
    async def test_mark_all_read(self, client, db, auth_headers):
        """全部标记已读"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        await client.post("/api/v1/notifications/batch", json={
            "user_ids": [user_id],
            "notification_type": "system",
            "title": "批量已读测试1",
        }, headers=auth_headers)
        await client.post("/api/v1/notifications/batch", json={
            "user_ids": [user_id],
            "notification_type": "system",
            "title": "批量已读测试2",
        }, headers=auth_headers)

        resp = await client.put("/api/v1/notifications/read-all", headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
        assert resp.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_delete_notification(self, client, db, auth_headers):
        """删除通知"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        await client.post("/api/v1/notifications/batch", json={
            "user_ids": [user_id],
            "notification_type": "system",
            "title": "待删除通知",
        }, headers=auth_headers)

        resp = await client.get("/api/v1/notifications/?limit=1", headers=auth_headers)
        notification_id = resp.json()["data"][0]["id"]

        resp = await client.delete(f"/api/v1/notifications/{notification_id}", headers=auth_headers)
        assert resp.status_code == 200

        resp = await client.get(f"/api/v1/notifications/{notification_id}/read", headers=auth_headers)
        # shouldn't exist anymore, mark_read returns 404
        # Actually we don't have a GET endpoint for single notification
        # Just verify it's gone from the list
        resp = await client.get("/api/v1/notifications/", headers=auth_headers)
        assert not any(n["id"] == notification_id for n in resp.json()["data"])

    @pytest.mark.asyncio
    async def test_filter_by_type(self, client, db, auth_headers):
        """按类型筛选通知"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = resp.json()["id"]

        await client.post("/api/v1/notifications/batch", json={
            "user_ids": [user_id],
            "notification_type": "payment_success",
            "title": "支付成功通知",
        }, headers=auth_headers)

        resp = await client.get("/api/v1/notifications/?notification_type=payment_success", headers=auth_headers)
        assert resp.status_code == 200
        assert all(n["notification_type"] == "payment_success" for n in resp.json()["data"])
