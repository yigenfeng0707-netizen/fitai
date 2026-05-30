"""
Celery 异步任务
"""
import os
from celery import Celery
from celery.schedules import crontab

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

celery_app = Celery(
    "fit_saas",
    broker=broker_url,
    backend=result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_routes={
        "backend.worker.send_reminder": {"queue": "reminders"},
        "backend.worker.generate_report": {"queue": "reports"},
    },
    beat_schedule={
        "expire-pending-orders": {
            "task": "backend.worker.expire_pending_orders",
            "schedule": crontab(minute="*/5"),
        },
        "check-subscription-expiry": {
            "task": "backend.worker.check_subscription_expiry",
            "schedule": crontab(minute="*/10"),
        },
    },
)


@celery_app.task(bind=True, max_retries=3)
def send_reminder(self, booking_id: int, reminder_type: str = "before_class"):
    """发送预约提醒（课程开始前通知会员）"""
    import asyncio
    from backend.database import AsyncSessionLocal
    from backend.models.booking import Booking
    from backend.models.member import Member
    from backend.models.notification import Notification, NotificationType
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()
            if not booking:
                return False

            member_result = await session.execute(
                select(Member).where(Member.id == booking.member_id)
            )
            member = member_result.scalar_one_or_none()
            if not member:
                return False

            title = "课程提醒" if reminder_type == "before_class" else "签到提醒"
            content = f"尊敬的会员，您预约的课程即将开始，请准时到场。"

            notification = Notification(
                title=title,
                content=content,
                notification_type=NotificationType.SYSTEM,
                user_id=booking.member_id,
                organization_id=booking.organization_id,
            )
            session.add(notification)
            await session.commit()
            return True

    try:
        return asyncio.run(_run())
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def generate_report(self, report_type: str, date: str):
    """生成报表（营收/会员/预约统计）"""
    import asyncio
    from backend.database import AsyncSessionLocal
    from sqlalchemy import select, func
    from backend.models.order import Order, OrderStatus
    from backend.models.member import Member, MemberStatus
    from backend.models.booking import Booking, BookingStatus
    from datetime import datetime

    async def _run():
        async with AsyncSessionLocal() as session:
            report_date = datetime.strptime(date, "%Y-%m-%d").date()

            # 营收统计
            revenue_result = await session.execute(
                select(func.sum(Order.actual_amount)).where(
                    Order.payment_status == OrderStatus.PAID,
                    func.date(Order.paid_at) == report_date,
                )
            )
            total_revenue = revenue_result.scalar() or 0

            # 新增会员
            new_members_result = await session.execute(
                select(func.count()).where(
                    func.date(Member.created_at) == report_date,
                )
            )
            new_members = new_members_result.scalar() or 0

            # 预约数
            bookings_result = await session.execute(
                select(func.count()).where(
                    func.date(Booking.created_at) == report_date,
                )
            )
            total_bookings = bookings_result.scalar() or 0

            # 签到数
            checkins_result = await session.execute(
                select(func.count()).where(
                    Booking.status == BookingStatus.CHECKED_IN,
                    func.date(Booking.check_in_time) == report_date,
                )
            )
            total_checkins = checkins_result.scalar() or 0

            report = {
                "report_type": report_type,
                "date": date,
                "revenue": float(total_revenue),
                "new_members": new_members,
                "total_bookings": total_bookings,
                "total_checkins": total_checkins,
                "checkin_rate": round(total_checkins / total_bookings * 100, 1) if total_bookings > 0 else 0,
            }

            from backend.logger import logger
            logger.info(f"Generated {report_type} report for {date}: {report}")
            return report

    return asyncio.run(_run())


@celery_app.task
def sync_member_data(member_id: int):
    """同步会员数据（会员卡余额/次数/有效期与交易记录对账）"""
    import asyncio
    from backend.database import AsyncSessionLocal
    from backend.models.member import Member
    from backend.models.card_transaction import CardTransaction, TransactionType
    from sqlalchemy import select, func

    async def _run():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Member).where(Member.id == member_id)
            )
            member = result.scalar_one_or_none()
            if not member:
                return {"status": "error", "message": "Member not found"}

            # 计算交易记录汇总
            balance_result = await session.execute(
                select(func.sum(CardTransaction.amount)).where(
                    CardTransaction.member_id == member_id,
                    CardTransaction.transaction_type == TransactionType.RECHARGE,
                )
            )
            total_recharge = balance_result.scalar() or 0

            consumption_result = await session.execute(
                select(func.sum(CardTransaction.amount)).where(
                    CardTransaction.member_id == member_id,
                    CardTransaction.transaction_type == TransactionType.CONSUME,
                )
            )
            total_consumption = consumption_result.scalar() or 0

            expected_balance = float(total_recharge) - float(total_consumption)

            # 检查并修正余额偏差
            current_balance = float(member.card_balance or 0)
            if abs(current_balance - expected_balance) > 0.01:
                from backend.logger import logger
                logger.warning(
                    f"Member {member_id} balance mismatch: "
                    f"current={current_balance}, expected={expected_balance}"
                )
                member.card_balance = expected_balance

            await session.commit()
            return {
                "status": "ok",
                "member_id": member_id,
                "balance_corrected": current_balance != expected_balance,
            }

    return asyncio.run(_run())


@celery_app.task
def expire_pending_orders():
    """Auto-cancel orders past expiration time."""
    import asyncio
    from backend.database import AsyncSessionLocal
    from backend.services.order import OrderService

    async def _run():
        async with AsyncSessionLocal() as session:
            expired = await OrderService.expire_pending_orders(session)
            await session.commit()
            return len(expired)

    count = asyncio.run(_run())
    if count:
        from backend.logger import logger
        logger.info(f"Expired {count} pending orders")
    return count


@celery_app.task
def check_subscription_expiry():
    """Check and handle subscription expiry/auto-renew."""
    import asyncio
    from backend.database import AsyncSessionLocal
    from backend.services.subscription import SubscriptionService

    async def _run():
        async with AsyncSessionLocal() as session:
            result = await SubscriptionService.check_expired(session)
            await session.commit()
            return len(result)

    count = asyncio.run(_run())
    if count:
        from backend.logger import logger
        logger.info(f"Processed {count} subscription expiry checks")
    return count