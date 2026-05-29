"""
API - 消息通知
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.notification import NotificationType
from backend.models.notification_template import NotificationTemplate
from backend.schemas.notification import (
    NotificationResponse,
    NotificationBatchCreate,
    UnreadCountResponse,
    SendNotificationRequest,
    BatchSendNotificationRequest,
    NotificationSendResult,
    NotificationBatchSendResult,
    NotificationTemplateCreate,
    NotificationTemplateResponse,
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


# ============ 多渠道通知推送端点 ============


@router.post("/send", response_model=NotificationSendResult)
async def send_notification(
    request: SendNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送通知（支持多渠道）"""
    from backend.services.notification_service import notification_dispatcher

    result = await notification_dispatcher.send(
        channels=request.channels,
        user_id=request.user_id,
        title=request.title,
        content=request.content,
        db=db,
        organization_id=current_user.organization_id,
        link=request.link,
        extra_data=request.extra_data,
    )
    return NotificationSendResult(
        success=result["success"],
        channel_results=result["results"],
        errors=result["errors"],
    )


@router.post("/send/batch", response_model=NotificationBatchSendResult)
async def send_batch_notification(
    request: BatchSendNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量发送通知"""
    from backend.services.notification_service import notification_dispatcher

    result = await notification_dispatcher.send_batch(
        channels=request.channels,
        user_ids=request.user_ids,
        title=request.title,
        content=request.content,
        db=db,
        organization_id=current_user.organization_id,
        link=request.link,
        extra_data=request.extra_data,
    )
    return NotificationBatchSendResult(
        success=result["success"],
        total=result["total"],
        success_count=result["success_count"],
        results=result["results"],
        errors=result["errors"],
    )


# ============ 通知模板端点 ============


@router.get("/templates", response_model=ListResponse[NotificationTemplateResponse])
async def get_notification_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取通知模板列表"""
    query = (
        select(NotificationTemplate)
        .where(NotificationTemplate.organization_id == current_user.organization_id)
        .order_by(NotificationTemplate.created_at.desc())
    )

    from sqlalchemy import func
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    result = await db.execute(query.offset(skip).limit(limit))
    templates = result.scalars().all()
    return ListResponse(data=templates, total=total, page=skip // limit + 1, page_size=limit)


@router.post("/templates", response_model=NotificationTemplateResponse)
async def create_notification_template(
    template: NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建通知模板"""
    from datetime import datetime

    # 检查 code 是否已存在
    existing = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.code == template.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="模板 code 已存在")

    db_template = NotificationTemplate(
        name=template.name,
        code=template.code,
        title_template=template.title_template,
        content_template=template.content_template,
        channels=template.channels,
        notification_type=template.notification_type,
        organization_id=current_user.organization_id,
    )
    db.add(db_template)
    await db.flush()
    await db.refresh(db_template)
    return db_template
