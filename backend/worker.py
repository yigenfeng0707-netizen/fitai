"""
Celery 异步任务
"""
import os
from celery import Celery

# 读取配置
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
)


@celery_app.task(bind=True, max_retries=3)
def send_reminder(self, booking_id: int, reminder_type: str = "before_class"):
    """发送预约提醒"""
    # TODO: 实现微信/短信通知
    pass


@celery_app.task(bind=True, max_retries=3)
def generate_report(self, report_type: str, date: str):
    """生成报表"""
    # TODO: 实现报表生成
    pass


@celery_app.task
def sync_member_data(member_id: int):
    """同步会员数据"""
    # TODO: 实现数据同步
    pass