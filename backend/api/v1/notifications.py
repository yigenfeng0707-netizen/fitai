"""
API - 消息通知
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.notification import NotificationType
from backend.schemas.notification import (
    NotificationResponse,
    NotificationBatchCreate,
    UnreadCountResponse,
)
from backend.schemas.common import BaseResponse, ListResponse

router = APIRouter()


@router.get("/", response_model=ListResponse[NotificationResponse])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.notification import NotificationCRUD
    notifications, total = await NotificationCRUD.get_list(
        db, current_user.id, current_user.organization_id, skip=skip, limit=limit,
        is_read=is_read, notification_type=notification_type,
    )
    return ListResponse(data=notifications, total=total, page=skip // limit + 1, page_size=limit)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.notification import NotificationCRUD
    count = await NotificationCRUD.get_unread_count(db, current_user.id, current_user.organization_id)
    return UnreadCountResponse(count=count)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.notification import NotificationCRUD
    notification = await NotificationCRUD.mark_read(db, notification_id, current_user.id, current_user.organization_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    return notification


@router.put("/read-all", response_model=BaseResponse)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.notification import NotificationCRUD
    count = await NotificationCRUD.mark_all_read(db, current_user.id, current_user.organization_id)
    return BaseResponse(message=f"已标记 {count} 条通知为已读")


@router.delete("/{notification_id}", response_model=BaseResponse)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.notification import NotificationCRUD
    deleted = await NotificationCRUD.delete(db, notification_id, current_user.id, current_user.organization_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="通知不存在")
    return BaseResponse(message="删除成功")


@router.post("/batch", response_model=BaseResponse)
async def batch_create_notifications(
    req: NotificationBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.notification import NotificationCRUD
    await NotificationCRUD.batch_create(
        db,
        user_ids=req.user_ids,
        notification_type=req.notification_type,
        title=req.title,
        content=req.content,
        link=req.link,
        extra_data=req.extra_data,
        organization_id=current_user.organization_id,
    )
    return BaseResponse(message=f"已发送 {len(req.user_ids)} 条通知")
