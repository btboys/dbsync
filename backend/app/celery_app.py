from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "dbsync",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    beat_schedule={
        "check-schedules": {
            "task": "check_schedules",
            "schedule": crontab(minute="*"),  # every minute
        },
    },
)
