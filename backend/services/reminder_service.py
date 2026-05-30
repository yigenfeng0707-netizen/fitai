"""
自动提醒服务 - 生日/到期自动提醒
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, and_, or_, func, not_, exists
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.member import Member, MemberStatus
from backend.models.notification import Notification, NotificationType
from backend.models.booking import Booking, BookingStatus
from backend.models.auth import User
from backend.crud.automation import AutomationCRUD
from backend.schemas.reminder import ReminderConfig, ReminderStats, ReminderBatchResult


class ReminderService:
    """自动提醒服务"""

    @staticmethod
    async def check_birthday_reminders(
        db: AsyncSession,
        organization_id: int,
        days_ahead: int = 7,
    ) -> list[dict]:
        """
        检查即将过生日的会员
        - 查找 birthday 在未来 days_ahead 天内的活跃会员
        - 返回匹配的会员列表
        """
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)

        # Filter in SQL: compute this-year and next-year birthday candidates
        # and check if they fall within the window.
        # SQLite: use date(birthday, 'start of year', '+N year') pattern.
        this_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        next_year_start = this_year_start.replace(year=this_year_start.year + 1)

        result = await db.execute(
            select(Member).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
                Member.birthday.isnot(None),
                or_(
                    # This year's birthday hasn't happened yet and is within window
                    and_(
                        func.date(Member.birthday, f"+{now.year - 1900} years") >= now.date(),
                        func.date(Member.birthday, f"+{now.year - 1900} years") <= end.date(),
                    ),
                    # Next year's birthday is within window
                    and_(
                        func.date(Member.birthday, f"+{now.year + 1 - 1900} years") >= now.date(),
                        func.date(Member.birthday, f"+{now.year + 1 - 1900} years") <= end.date(),
                    ),
                ),
            )
        )
        members = result.scalars().all()

        matched = []
        for member in members:
            birthday = member.birthday
            try:
                this_year_birthday = birthday.replace(year=now.year)
            except ValueError:
                this_year_birthday = birthday.replace(year=now.year, day=28)

            if this_year_birthday < now:
                try:
                    next_birthday = birthday.replace(year=now.year + 1)
                except ValueError:
                    next_birthday = birthday.replace(year=now.year + 1, day=28)
            else:
                next_birthday = this_year_birthday

            if now <= next_birthday <= end:
                days_until = (next_birthday.date() - now.date()).days
                matched.append({
                    "member_id": member.id,
                    "member_name": member.name,
                    "phone": member.phone,
                    "type": "birthday",
                    "trigger_date": next_birthday.date(),
                    "days_until": days_until,
                })

        return matched

    @staticmethod
    async def check_card_expiry_reminders(
        db: AsyncSession,
        organization_id: int,
        days_ahead: int = 30,
    ) -> list[dict]:
        """
        检查即将到期的会员卡
        - 查找 card_end_date 在未来 days_ahead 天内的活跃会员
        - 返回匹配的会员列表
        """
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)

        result = await db.execute(
            select(Member).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
                Member.card_end_date.isnot(None),
                Member.card_end_date >= now,
                Member.card_end_date <= end,
            )
        )
        members = result.scalars().all()

        matched = []
        for member in members:
            days_until = (member.card_end_date.date() - now.date()).days
            matched.append({
                "member_id": member.id,
                "member_name": member.name,
                "phone": member.phone,
                "type": "expiry",
                "trigger_date": member.card_end_date.date(),
                "days_until": days_until,
            })

        return matched

    @staticmethod
    async def check_card_expired_reminders(
        db: AsyncSession,
        organization_id: int,
        days_after: int = 7,
    ) -> list[dict]:
        """
        检查已过期但未续费的会员卡
        - 查找 card_end_date 在过去 days_after 天内且状态仍为 active 的会员
        - 返回匹配的会员列表
        """
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days_after)

        result = await db.execute(
            select(Member).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
                Member.card_end_date.isnot(None),
                Member.card_end_date < now,
                Member.card_end_date >= start,
            )
        )
        members = result.scalars().all()

        matched = []
        for member in members:
            days_since = (now.date() - member.card_end_date.date()).days
            matched.append({
                "member_id": member.id,
                "member_name": member.name,
                "phone": member.phone,
                "type": "expired",
                "trigger_date": member.card_end_date.date(),
                "days_until": -days_since,
            })

        return matched

    @staticmethod
    async def check_no_visit_reminder(
        db: AsyncSession,
        organization_id: int,
        no_visit_days: int = 30,
    ) -> list[dict]:
        """
        检查长时间未到店的会员
        - 查找最近 no_visit_days 天内没有预约/签到记录的活跃会员
        - 返回匹配的会员列表
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=no_visit_days)

        # Batch: get all active members with their recent booking count and last visit
        result = await db.execute(
            select(
                Member.id,
                Member.name,
                Member.phone,
                Member.created_at,
                func.count(Booking.id).label("recent_booking_count"),
                func.max(Booking.created_at).label("last_booking_at"),
            )
            .outerjoin(Booking, and_(
                Booking.member_id == Member.id,
                Booking.organization_id == organization_id,
                Booking.created_at >= cutoff,
                Booking.status.in_([
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                    BookingStatus.CHECKED_IN,
                    BookingStatus.COMPLETED,
                ]),
            ))
            .where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
            )
            .group_by(Member.id, Member.name, Member.phone, Member.created_at)
        )

        matched = []
        for row in result:
            if row.recent_booking_count == 0:
                last_visit = row.last_booking_at
                last_visit_date = last_visit.date() if last_visit else None
                matched.append({
                    "member_id": row.id,
                    "member_name": row.name,
                    "phone": row.phone,
                    "type": "no_visit",
                    "trigger_date": last_visit_date or row.created_at.date(),
                    "days_until": -no_visit_days,
                })

        return matched

    @staticmethod
    async def send_birthday_wishes(
        db: AsyncSession,
        member: dict,
        organization_id: int,
    ) -> dict:
        """
        发送生日祝福
        - 创建站内通知
        - 记录到自动化日志
        - 返回发送结果
        """
        # 查找关联的用户（教练/管理员）
        target_user_ids = await ReminderService._resolve_target_users(
            db, organization_id, member["member_id"],
        )

        title = f"生日快乐！{member['member_name']}的生日即将到来"
        content = (
            f"会员 {member['member_name']}（{member['phone']}）的生日在 "
            f"{member['days_until']} 天后，请及时送上祝福！"
        )

        notifications = []
        for user_id in target_user_ids:
            notification = Notification(
                user_id=user_id,
                organization_id=organization_id,
                notification_type=NotificationType.MARKETING,
                title=title,
                content=content,
                extra_data={
                    "reminder_type": "birthday",
                    "member_id": member["member_id"],
                    "member_name": member["member_name"],
                    "days_until": member["days_until"],
                },
            )
            db.add(notification)
            notifications.append(notification)

        await db.flush()

        return {
            "member_id": member["member_id"],
            "type": "birthday",
            "notifications_sent": len(notifications),
            "status": "success",
        }

    @staticmethod
    async def send_expiry_reminder(
        db: AsyncSession,
        member: dict,
        organization_id: int,
        days_left: int,
    ) -> dict:
        """
        发送到期提醒
        - 创建站内通知
        - 记录到自动化日志
        """
        target_user_ids = await ReminderService._resolve_target_users(
            db, organization_id, member["member_id"],
        )

        reminder_type = member["type"]
        if reminder_type == "expired":
            title = f"会员卡已过期：{member['member_name']}"
            notification_type = NotificationType.CARD_EXPIRED
            content = (
                f"会员 {member['member_name']}（{member['phone']}）的会员卡已过期 "
                f"{abs(member['days_until'])} 天，建议及时联系续费。"
            )
        else:
            title = f"会员卡即将到期：{member['member_name']}"
            notification_type = NotificationType.CARD_EXPIRING
            content = (
                f"会员 {member['member_name']}（{member['phone']}）的会员卡将在 "
                f"{member['days_until']} 天后到期，建议提前联系续费。"
            )

        notifications = []
        for user_id in target_user_ids:
            notification = Notification(
                user_id=user_id,
                organization_id=organization_id,
                notification_type=notification_type,
                title=title,
                content=content,
                extra_data={
                    "reminder_type": reminder_type,
                    "member_id": member["member_id"],
                    "member_name": member["member_name"],
                    "days_until": member["days_until"],
                },
            )
            db.add(notification)
            notifications.append(notification)

        await db.flush()

        return {
            "member_id": member["member_id"],
            "type": reminder_type,
            "notifications_sent": len(notifications),
            "status": "success",
        }

    @staticmethod
    async def send_no_visit_reminder(
        db: AsyncSession,
        member: dict,
        organization_id: int,
    ) -> dict:
        """
        发送未到店提醒
        - 创建站内通知
        """
        target_user_ids = await ReminderService._resolve_target_users(
            db, organization_id, member["member_id"],
        )

        title = f"会员长时间未到店：{member['member_name']}"
        content = (
            f"会员 {member['member_name']}（{member['phone']}）已有 "
            f"{abs(member['days_until'])} 天未到店，建议主动联系跟进。"
        )

        notifications = []
        for user_id in target_user_ids:
            notification = Notification(
                user_id=user_id,
                organization_id=organization_id,
                notification_type=NotificationType.MARKETING,
                title=title,
                content=content,
                extra_data={
                    "reminder_type": "no_visit",
                    "member_id": member["member_id"],
                    "member_name": member["member_name"],
                    "no_visit_days": abs(member["days_until"]),
                },
            )
            db.add(notification)
            notifications.append(notification)

        await db.flush()

        return {
            "member_id": member["member_id"],
            "type": "no_visit",
            "notifications_sent": len(notifications),
            "status": "success",
        }

    @staticmethod
    async def process_all_reminders(
        db: AsyncSession,
        organization_id: int,
        config: Optional[ReminderConfig] = None,
    ) -> ReminderBatchResult:
        """
        处理所有提醒（一次性调用）
        - 检查生日、到期、过期、未到店
        - 对匹配的会员发送相应通知
        - 返回处理统计
        """
        if config is None:
            config = ReminderConfig()

        stats = ReminderStats()
        errors: list[str] = []

        # 1. 生日提醒
        if config.birthday_enabled:
            try:
                birthday_members = await ReminderService.check_birthday_reminders(
                    db, organization_id, days_ahead=config.birthday_days_ahead,
                )
                stats.birthday_count = len(birthday_members)
                for member in birthday_members:
                    try:
                        result = await ReminderService.send_birthday_wishes(
                            db, member, organization_id,
                        )
                        stats.total_notifications_sent += result["notifications_sent"]
                    except Exception as e:
                        errors.append(f"生日提醒发送失败 [会员{member['member_id']}]: {str(e)}")
            except Exception as e:
                errors.append(f"生日提醒检查失败: {str(e)}")

        # 2. 到期提醒
        if config.expiry_enabled:
            try:
                expiry_members = await ReminderService.check_card_expiry_reminders(
                    db, organization_id, days_ahead=config.expiry_days_ahead,
                )
                stats.expiry_count = len(expiry_members)
                for member in expiry_members:
                    try:
                        result = await ReminderService.send_expiry_reminder(
                            db, member, organization_id,
                            days_left=member["days_until"],
                        )
                        stats.total_notifications_sent += result["notifications_sent"]
                    except Exception as e:
                        errors.append(f"到期提醒发送失败 [会员{member['member_id']}]: {str(e)}")
            except Exception as e:
                errors.append(f"到期提醒检查失败: {str(e)}")

        # 3. 过期提醒
        if config.expired_enabled:
            try:
                expired_members = await ReminderService.check_card_expired_reminders(
                    db, organization_id, days_after=config.expired_days_after,
                )
                stats.expired_count = len(expired_members)
                for member in expired_members:
                    try:
                        result = await ReminderService.send_expiry_reminder(
                            db, member, organization_id,
                            days_left=member["days_until"],
                        )
                        stats.total_notifications_sent += result["notifications_sent"]
                    except Exception as e:
                        errors.append(f"过期提醒发送失败 [会员{member['member_id']}]: {str(e)}")
            except Exception as e:
                errors.append(f"过期提醒检查失败: {str(e)}")

        # 4. 未到店提醒
        if config.no_visit_enabled:
            try:
                no_visit_members = await ReminderService.check_no_visit_reminder(
                    db, organization_id, no_visit_days=config.no_visit_days,
                )
                stats.no_visit_count = len(no_visit_members)
                for member in no_visit_members:
                    try:
                        result = await ReminderService.send_no_visit_reminder(
                            db, member, organization_id,
                        )
                        stats.total_notifications_sent += result["notifications_sent"]
                    except Exception as e:
                        errors.append(f"未到店提醒发送失败 [会员{member['member_id']}]: {str(e)}")
            except Exception as e:
                errors.append(f"未到店提醒检查失败: {str(e)}")

        return ReminderBatchResult(
            processed=stats,
            notifications_created=stats.total_notifications_sent,
            errors=errors,
        )

    @staticmethod
    async def _resolve_target_users(
        db: AsyncSession,
        organization_id: int,
        member_id: int,
    ) -> list[int]:
        """
        解析提醒通知的目标用户
        - 会员关联的教练
        - 门店管理员
        """
        user_ids = set()

        # 查找会员关联的教练
        member_result = await db.execute(
            select(Member).where(Member.id == member_id)
        )
        member = member_result.scalar_one_or_none()
        if member and member.coach_id:
            coach_user = await db.execute(
                select(User).where(
                    User.coach_id == member.coach_id,
                    User.organization_id == organization_id,
                    User.is_active.is_(True),
                )
            )
            coach = coach_user.scalar_one_or_none()
            if coach:
                user_ids.add(coach.id)

        # 查找门店管理员
        admins = await db.execute(
            select(User.id).where(
                User.organization_id == organization_id,
                User.is_active.is_(True),
                User.role.in_(["super_admin", "store_owner"]),
            )
        )
        for row in admins:
            user_ids.add(row[0])

        return list(user_ids)
