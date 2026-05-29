"""
Pydantic Schema - 消息通知
"""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field

from backend.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    notification_type: NotificationType
    title: str
    content: Optional[str] = None
    is_read: bool
    link: Optional[str] = None
    extra_data: Optional[Any] = None
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: int
    notification_type: NotificationType = NotificationType.SYSTEM
    title: str = Field(..., max_length=200)
    content: Optional[str] = None
    link: Optional[str] = None
    extra_data: Optional[Any] = None


class NotificationBatchCreate(BaseModel):
    user_ids: list[int]
    notification_type: NotificationType = NotificationType.SYSTEM
    title: str = Field(..., max_length=200)
    content: Optional[str] = None
    link: Optional[str] = None
    extra_data: Optional[Any] = None


class UnreadCountResponse(BaseModel):
    count: int


# ============ 多渠道通知推送 Schema ============


class SendNotificationRequest(BaseModel):
    user_id: int
    title: str
    content: str
    channels: list[str] = ["in_app"]
    link: Optional[str] = None
    extra_data: Optional[dict] = None


class BatchSendNotificationRequest(BaseModel):
    user_ids: list[int] = Field(..., min_length=1, max_length=500)
    title: str
    content: str
    channels: list[str] = ["in_app"]
    link: Optional[str] = None
    extra_data: Optional[dict] = None


class NotificationSendResult(BaseModel):
    success: bool
    channel_results: dict
    errors: list[str]


class NotificationBatchSendResult(BaseModel):
    success: bool
    total: int
    success_count: int
    results: dict
    errors: list[str]


# ============ 通知模板 Schema ============


class NotificationTemplateBase(BaseModel):
    name: str
    code: str
    title_template: str
    content_template: str
    channels: list[str] = ["in_app"]
    notification_type: str = "system"


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateResponse(NotificationTemplateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
