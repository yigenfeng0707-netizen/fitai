from celery import Celery
from app.settings import settings

celery = Celery(
    "fitai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)