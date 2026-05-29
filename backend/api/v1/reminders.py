"""API - 自动提醒（生日/到期）"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user, create_permission_checker
from backend.models.auth import User
from backend.schemas.reminder import ReminderConfig, ReminderPreviewItem, ReminderStats
from backend.services.reminder_service import ReminderService

router = APIRouter()


@router.get("/preview")
async def preview_reminders(
    type: Optional[str] = Query(None, pattern="^(birthday|expiry|expired|no_visit)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """预览即将触发的提醒"""
    config = ReminderConfig()
    organization_id = current_user.organization_id
    results = []

    if type is None or type == "birthday":
        if config.birthday_enabled:
            results.extend(
                await ReminderService.check_birthday_reminders(
                    db, organization_id, days_ahead=config.birthday_days_ahead,
                )
            )

    if type is None or type == "expiry":
        if config.expiry_enabled:
            results.extend(
                await ReminderService.check_card_expiry_reminders(
                    db, organization_id, days_ahead=config.expiry_days_ahead,
                )
            )

    if type is None or type == "expired":
        if config.expired_enabled:
            results.extend(
                await ReminderService.check_card_expired_reminders(
                    db, organization_id, days_after=config.expired_days_after,
                )
            )

    if type is None or type == "no_visit":
        if config.no_visit_enabled:
            results.extend(
                await ReminderService.check_no_visit_reminder(
                    db, organization_id, no_visit_days=config.no_visit_days,
                )
            )

    return {
        "success": True,
        "message": "ok",
        "data": [ReminderPreviewItem(**item).model_dump() for item in results],
        "total": len(results),
    }


@router.get("/stats")
async def get_reminder_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取提醒统计"""
    config = ReminderConfig()
    organization_id = current_user.organization_id

    birthday_count = 0
    expiry_count = 0
    expired_count = 0
    no_visit_count = 0

    if config.birthday_enabled:
        birthday_count = len(
            await ReminderService.check_birthday_reminders(
                db, organization_id, days_ahead=config.birthday_days_ahead,
            )
        )

    if config.expiry_enabled:
        expiry_count = len(
            await ReminderService.check_card_expiry_reminders(
                db, organization_id, days_ahead=config.expiry_days_ahead,
            )
        )

    if config.expired_enabled:
        expired_count = len(
            await ReminderService.check_card_expired_reminders(
                db, organization_id, days_after=config.expired_days_after,
            )
        )

    if config.no_visit_enabled:
        no_visit_count = len(
            await ReminderService.check_no_visit_reminder(
                db, organization_id, no_visit_days=config.no_visit_days,
            )
        )

    stats = ReminderStats(
        birthday_count=birthday_count,
        expiry_count=expiry_count,
        expired_count=expired_count,
        no_visit_count=no_visit_count,
    )

    return {
        "success": True,
        "message": "ok",
        "data": stats.model_dump(),
    }


@router.post("/execute")
async def execute_reminders(
    config: Optional[ReminderConfig] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(create_permission_checker("marketing:write")),
):
    """手动执行提醒（需要营销权限）"""
    result = await ReminderService.process_all_reminders(
        db, organization_id=current_user.organization_id,
        config=config,
    )

    return {
        "success": True,
        "message": f"已发送 {result.notifications_created} 条通知",
        "data": {
            "processed": result.processed.model_dump(),
            "notifications_created": result.notifications_created,
            "errors": result.errors,
        },
    }


@router.get("/config")
async def get_reminder_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取提醒配置（返回默认配置）"""
    config = ReminderConfig()
    return {
        "success": True,
        "message": "ok",
        "data": config.model_dump(),
    }


@router.put("/config")
async def update_reminder_config(
    config: ReminderConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(create_permission_checker("marketing:write")),
):
    """更新提醒配置"""
    # 当前配置直接通过请求体传入，后续可持久化到数据库
    return {
        "success": True,
        "message": "配置已更新",
        "data": config.model_dump(),
    }
