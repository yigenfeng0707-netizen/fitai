"""
Pydantic Schema - 自动提醒
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ReminderConfig(BaseModel):
    """提醒配置"""
    birthday_days_ahead: int = Field(default=7, ge=1, le=365, description="提前几天提醒生日")
    expiry_days_ahead: int = Field(default=30, ge=1, le=365, description="提前几天提醒到期")
    expired_days_after: int = Field(default=7, ge=1, le=365, description="过期后几天内仍提醒")
    no_visit_days: int = Field(default=30, ge=1, le=365, description="多少天未到店触发提醒")
    birthday_enabled: bool = Field(default=True, description="是否启用生日提醒")
    expiry_enabled: bool = Field(default=True, description="是否启用到期提醒")
    expired_enabled: bool = Field(default=True, description="是否启用过期提醒")
    no_visit_enabled: bool = Field(default=True, description="是否启用未到店提醒")


class ReminderPreviewItem(BaseModel):
    """提醒预览条目"""
    member_id: int
    member_name: str
    phone: str
    type: str = Field(..., description="提醒类型: birthday, expiry, expired, no_visit")
    trigger_date: date = Field(..., description="触发日期（生日或到期日）")
    days_until: int = Field(..., description="距触发日天数（负数为已过期）")


class ReminderStats(BaseModel):
    """提醒统计"""
    birthday_count: int = 0
    expiry_count: int = 0
    expired_count: int = 0
    no_visit_count: int = 0
    total_notifications_sent: int = 0


class ReminderBatchResult(BaseModel):
    """批量提醒执行结果"""
    processed: ReminderStats
    notifications_created: int = 0
    errors: list[str] = Field(default_factory=list)
