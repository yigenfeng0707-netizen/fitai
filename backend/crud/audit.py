"""
CRUD - 操作日志
"""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.auth import AuditLog
from backend.schemas.audit import AuditLogCreate


class AuditLogCRUD:
    @staticmethod
    async def create(
        db: AsyncSession,
        obj_in: AuditLogCreate,
        user_id: Optional[int] = None,
        organization_id: int = 1,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=obj_in.action,
            resource=obj_in.resource,
            resource_id=obj_in.resource_id,
            detail=obj_in.detail,
            old_value=obj_in.old_value,
            new_value=obj_in.new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def get_list(
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[int] = None,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog).where(AuditLog.organization_id == organization_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource:
            query = query.where(AuditLog.resource == resource)
        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)
        query = query.order_by(AuditLog.created_at.desc())

        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total
