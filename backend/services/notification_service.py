"""
通知推送服务 - 统一多渠道通知分发
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """通知渠道抽象基类"""

    @abstractmethod
    async def send(self, user_id: int, title: str, content: str, **kwargs) -> bool:
        """
        发送通知
        Returns: True 表示发送成功，False 表示失败
        """
        pass


class InAppChannel(NotificationChannel):
    """站内通知渠道 - 创建数据库记录"""

    async def send(self, user_id: int, title: str, content: str,
                   link: Optional[str] = None, extra_data: Optional[dict] = None,
                   db: Optional[AsyncSession] = None, organization_id: int = 1,
                   notification_type: NotificationType = NotificationType.SYSTEM,
                   **kwargs) -> bool:
        if db is None:
            logger.warning("InAppChannel: db session is None, skipping in-app notification")
            return False

        try:
            notification = Notification(
                user_id=user_id,
                organization_id=organization_id,
                notification_type=notification_type,
                title=title,
                content=content,
                link=link,
                extra_data=extra_data,
            )
            db.add(notification)
            await db.flush()
            logger.info(f"InAppChannel: notification created for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"InAppChannel: failed to create notification for user {user_id}: {e}")
            return False


class SMSChannel(NotificationChannel):
    """短信通知渠道 - 支持阿里云短信 API"""

    async def send(self, user_id: int, title: str, content: str,
                   phone: Optional[str] = None, db: Optional[AsyncSession] = None,
                   organization_id: int = 1, **kwargs) -> bool:
        if not settings.SMS_ENABLED:
            logger.info(f"SMSChannel: SMS is disabled, skipping SMS for user {user_id}")
            return False

        try:
            # 获取会员手机号
            if not phone and db:
                from sqlalchemy import select
                from backend.models.member import Member
                result = await db.execute(
                    select(Member.phone).where(Member.id == user_id)
                )
                phone = result.scalar_one_or_none()

            if not phone:
                logger.warning(f"SMSChannel: no phone number for user {user_id}")
                return False

            # 阿里云短信 API
            import httpx
            import hashlib
            import hmac
            import base64
            import urllib.parse
            import time
            import uuid

            access_key = getattr(settings, 'SMS_ACCESS_KEY', '')
            access_secret = getattr(settings, 'SMS_ACCESS_SECRET', '')
            sign_name = getattr(settings, 'SMS_SIGN_NAME', '')
            template_code = getattr(settings, 'SMS_TEMPLATE_CODE', '')
            sms_endpoint = "https://dysmsapi.aliyuncs.com"

            if not all([access_key, access_secret, sign_name, template_code]):
                logger.warning("SMSChannel: SMS credentials not configured")
                return False

            # 构建阿里云 API 签名
            params = {
                "PhoneNumbers": phone,
                "SignName": sign_name,
                "TemplateCode": template_code,
                "TemplateParam": f'{{"content":"{content}"}}',
                "AccessKeyId": access_key,
                "SignatureMethod": "HMAC-SHA1",
                "SignatureNonce": str(uuid.uuid4()),
                "SignatureVersion": "1.0",
                "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "Format": "JSON",
                "Action": "SendSms",
                "Version": "2017-05-25",
            }

            # 排序并签名
            sorted_params = sorted(params.items())
            canonical_query = urllib.parse.urlencode(sorted_params)
            string_to_sign = f"GET&%2F&{urllib.parse.quote(canonical_query, safe='')}"
            signature = base64.b64encode(
                hmac.new(
                    (access_secret + "&").encode(),
                    string_to_sign.encode(),
                    hashlib.sha1
                ).digest()
            ).decode()
            params["Signature"] = signature

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(sms_endpoint, params=params)
                result = response.json()
                if result.get("Code") == "OK":
                    logger.info(f"SMSChannel: SMS sent to {phone} for user {user_id}")
                    return True
                else:
                    logger.error(f"SMSChannel: API error {result.get('Code')}: {result.get('Message')}")
                    return False

        except Exception as e:
            logger.error(f"SMSChannel: failed to send SMS to user {user_id}: {e}")
            return False


class WeChatWorkChannel(NotificationChannel):
    """企业微信通知渠道 - 支持企业微信 API"""

    async def send(self, user_id: int, title: str, content: str,
                   db: Optional[AsyncSession] = None, organization_id: int = 1,
                   **kwargs) -> bool:
        if not settings.WECHAT_WORK_ENABLED:
            logger.info(f"WeChatWorkChannel: WeChat Work is disabled, skipping for user {user_id}")
            return False

        try:
            corp_id = getattr(settings, 'WECHAT_WORK_CORP_ID', '')
            agent_id = getattr(settings, 'WECHAT_WORK_AGENT_ID', '')
            secret = getattr(settings, 'WECHAT_WORK_SECRET', '')

            if not all([corp_id, agent_id, secret]):
                logger.warning("WeChatWorkChannel: WeChat Work credentials not configured")
                return False

            # 获取 access_token
            import httpx
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={secret}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                token_resp = await client.get(token_url)
                token_data = token_resp.json()
                if token_data.get("errcode") != 0:
                    logger.error(f"WeChatWorkChannel: token error {token_data.get('errmsg')}")
                    return False

                access_token = token_data["access_token"]

                # 发送应用消息
                # 需要用户在企业微信中的 userid，这里用 user_id 作为占位
                send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
                payload = {
                    "touser": str(user_id),
                    "msgtype": "text",
                    "agentid": int(agent_id),
                    "text": {
                        "content": f"{title}\n{content}" if title else content,
                    },
                }

                send_resp = await client.post(send_url, json=payload)
                send_data = send_resp.json()
                if send_data.get("errcode") == 0:
                    logger.info(f"WeChatWorkChannel: message sent to user {user_id}")
                    return True
                else:
                    logger.error(f"WeChatWorkChannel: send error {send_data.get('errmsg')}")
                    return False

        except Exception as e:
            logger.error(f"WeChatWorkChannel: failed to send to user {user_id}: {e}")
            return False


class NotificationDispatcher:
    """统一通知分发器 - 通过多个渠道发送通知"""

    def __init__(self):
        self._channels: dict[str, NotificationChannel] = {}

    def register_channel(self, name: str, channel: NotificationChannel):
        """注册通知渠道"""
        self._channels[name] = channel
        logger.info(f"NotificationDispatcher: registered channel '{name}'")

    def unregister_channel(self, name: str):
        """取消注册通知渠道"""
        self._channels.pop(name, None)

    def get_registered_channels(self) -> list[str]:
        """获取已注册的渠道列表"""
        return list(self._channels.keys())

    async def send(self, channels: list[str], user_id: int, title: str,
                   content: str, db: Optional[AsyncSession] = None,
                   organization_id: int = 1, **kwargs) -> dict:
        """
        通过多个渠道发送通知

        Args:
            channels: 渠道名称列表，如 ["in_app", "sms", "wechat_work"]
            user_id: 目标用户 ID
            title: 通知标题
            content: 通知内容
            db: 数据库会话（站内通知需要）
            organization_id: 组织 ID（多租户过滤）
            **kwargs: 额外参数（link, extra_data, phone 等）

        Returns:
            {"success": bool, "results": {"in_app": True, ...}, "errors": []}
        """
        results: dict[str, bool] = {}
        errors: list[str] = []

        for channel_name in channels:
            channel = self._channels.get(channel_name)
            if channel is None:
                errors.append(f"Channel '{channel_name}' not registered")
                results[channel_name] = False
                continue

            try:
                success = await channel.send(
                    user_id=user_id,
                    title=title,
                    content=content,
                    db=db,
                    organization_id=organization_id,
                    **kwargs,
                )
                results[channel_name] = success
                if not success:
                    errors.append(f"Failed to send via channel '{channel_name}'")
            except Exception as e:
                results[channel_name] = False
                errors.append(f"Channel '{channel_name}' error: {str(e)}")
                logger.error(f"NotificationDispatcher: channel '{channel_name}' error for user {user_id}: {e}")

        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
        }

    async def send_batch(self, channels: list[str], user_ids: list[int],
                         title: str, content: str, db: Optional[AsyncSession] = None,
                         organization_id: int = 1, **kwargs) -> dict:
        """
        批量发送通知

        Args:
            channels: 渠道名称列表
            user_ids: 目标用户 ID 列表
            title: 通知标题
            content: 通知内容
            db: 数据库会话
            organization_id: 组织 ID
            **kwargs: 额外参数

        Returns:
            {"success": bool, "total": int, "results": {"user_id": {...}, ...}, "errors": []}
        """
        import asyncio

        total = len(user_ids)
        batch_results: dict = {}
        errors: list[str] = []
        success_count = 0

        for user_id in user_ids:
            result = await self.send(
                channels=channels,
                user_id=user_id,
                title=title,
                content=content,
                db=db,
                organization_id=organization_id,
                **kwargs,
            )
            batch_results[str(user_id)] = result
            if result["success"]:
                success_count += 1
            else:
                errors.extend([f"User {user_id}: {e}" for e in result["errors"]])

        return {
            "success": success_count == total,
            "total": total,
            "success_count": success_count,
            "results": batch_results,
            "errors": errors,
        }


# 全局分发器实例 - 自动注册所有渠道
notification_dispatcher = NotificationDispatcher()
notification_dispatcher.register_channel("in_app", InAppChannel())
notification_dispatcher.register_channel("sms", SMSChannel())
notification_dispatcher.register_channel("wechat_work", WeChatWorkChannel())


def setup_notification_channels() -> NotificationDispatcher:
    """初始化通知渠道并返回配置好的分发器"""
    dispatcher = NotificationDispatcher()
    dispatcher.register_channel("in_app", InAppChannel())
    dispatcher.register_channel("sms", SMSChannel())
    dispatcher.register_channel("wechat_work", WeChatWorkChannel())
    return dispatcher
