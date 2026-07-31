"""
API - 操作日志
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.schemas.audit import AuditLogResponse, AuditLogCreate
from backend.schemas.common import ListResponse

router = APIRouter()


@router.get("/", response_model=ListResponse[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.audit import AuditLogCRUD
    logs, total = await AuditLogCRUD.get_list(
        db, current_user.organization_id,
        skip=skip, limit=limit,
        user_id=user_id, action=action,
        resource=resource, resource_id=resource_id,
    )
    return ListResponse(data=logs, total=total, page=skip // limit + 1, page_size=limit)


@router.post("/", response_model=AuditLogResponse)
async def create_audit_log(
    obj_in: AuditLogCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.audit import AuditLogCRUD
    log = await AuditLogCRUD.create(
        db, obj_in,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return log
