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
    """发送预约提醒"""
    pass


@celery_app.task(bind=True, max_retries=3)
def generate_report(self, report_type: str, date: str):
    """生成报表"""
    pass


@celery_app.task
def sync_member_data(member_id: int):
    """同步会员数据"""
    pass


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