"""
Pydantic Schema - 操作日志
"""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel



class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource: Optional[str] = None
    resource_id: Optional[int] = None
    detail: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    action: str
    resource: Optional[str] = None
    resource_id: Optional[int] = None
    detail: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
