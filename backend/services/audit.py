"""
审计日志服务 - 快捷记录操作日志
"""
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.auth import AuditLog


class AuditService:
    @staticmethod
    async def log(
        db: AsyncSession,
        action: str,
        resource: str,
        resource_id: Optional[int] = None,
        detail: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        user_id: Optional[int] = None,
        organization_id: int = 1,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            detail=detail,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        db.add(log)
        await db.flush()
        return log
