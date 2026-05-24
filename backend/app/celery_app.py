from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "dbsync",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

from celery.schedules import crontab


class DynamicSchedule:
    """Loads backup schedules from DB on each beat tick."""

    def __call__(self):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import Session
        from app.models import BackupTask

        engine = create_engine(settings.database_url.replace("+aiomysql", "+pymysql"))
        session = Session(engine)
        try:
            tasks = session.execute(
                select(BackupTask).where(
                    BackupTask.is_enabled == True,
                    BackupTask.schedule_config.isnot(None),
                )
            ).scalars().all()

            schedule = {}
            for task in tasks:
                cron = task.schedule_config.get("cron")
                if not cron:
                    continue
                parts = cron.split()
                if len(parts) == 5:
                    minute, hour, day, month, week = parts
                    schedule[f"backup_{task.id}"] = {
                        "task": "run_backup_scheduled",
                        "schedule": crontab(
                            minute=minute, hour=hour,
                            day_of_month=day, month_of_year=month,
                            day_of_week=week,
                        ),
                        "args": (task.id,),
                    }
            return schedule
        finally:
            session.close()


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule=DynamicSchedule(),
)
