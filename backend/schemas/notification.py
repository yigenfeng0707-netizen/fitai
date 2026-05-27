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
