"""
CRUD - 消息通知
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import Notification, NotificationType
from backend.schemas.notification import NotificationCreate


class NotificationCRUD:
    @staticmethod
    async def create(
        db: AsyncSession,
        obj_in: NotificationCreate,
        organization_id: int,
    ) -> Notification:
        notification = Notification(
            user_id=obj_in.user_id,
            organization_id=organization_id,
            notification_type=obj_in.notification_type,
            title=obj_in.title,
            content=obj_in.content,
            link=obj_in.link,
            extra_data=obj_in.extra_data,
        )
        db.add(notification)
        await db.flush()
        return notification

    @staticmethod
    async def batch_create(
        db: AsyncSession,
        user_ids: list[int],
        notification_type: NotificationType,
        title: str,
        content: Optional[str] = None,
        link: Optional[str] = None,
        extra_data: Optional[dict] = None,
        organization_id: int = 1,
    ) -> list[Notification]:
        notifications = []
        for uid in user_ids:
            n = Notification(
                user_id=uid,
                organization_id=organization_id,
                notification_type=notification_type,
                title=title,
                content=content,
                link=link,
                extra_data=extra_data,
            )
            db.add(n)
            notifications.append(n)
        await db.flush()
        return notifications

    @staticmethod
    async def get_list(
        db: AsyncSession,
        user_id: int,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        is_read: Optional[bool] = None,
        notification_type: Optional[NotificationType] = None,
    ) -> tuple[list[Notification], int]:
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.organization_id == organization_id,
        )
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        query = query.order_by(Notification.created_at.desc())

        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: int, organization_id: int) -> int:
        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def mark_read(db: AsyncSession, notification_id: int, user_id: int, organization_id: int) -> Optional[Notification]:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await db.flush()
        return notification

    @staticmethod
    async def mark_all_read(db: AsyncSession, user_id: int, organization_id: int) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await db.flush()
        return result.rowcount

    @staticmethod
    async def delete(db: AsyncSession, notification_id: int, user_id: int, organization_id: int) -> bool:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.organization_id == organization_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification:
            await db.delete(notification)
            await db.flush()
            return True
        return False
