import datetime
import hashlib
import os
import subprocess
import tempfile

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.config import settings
from app.core.security import decrypt_password
from app.models import BackupTask, BackupRecord, TaskLog, Datasource
from app.worker.engines.base import ConnectionInfo


def _sync_get_db():
    engine = create_engine(settings.database_url.replace("+aiomysql", "+pymysql"))
    return Session(engine)


def _log(task_type: str, record_id: int, level: str, msg: str, db: Session):
    db.add(TaskLog(task_type=task_type, task_record_id=record_id, level=level, message=msg))
    db.commit()


def _get_engine(db_type: str):
    from app.worker.engines.mysql import MySQLEngine
    from app.worker.engines.postgresql import PostgreSQLEngine
    if db_type == "mysql":
        return MySQLEngine()
    elif db_type == "postgresql":
        return PostgreSQLEngine()
    raise ValueError(f"Unsupported database type: {db_type}")


@celery_app.task(bind=True, name="run_backup")
def run_backup(self, record_id: int):
    db = _sync_get_db()
    try:
        record = db.execute(select(BackupRecord).where(BackupRecord.id == record_id)).scalar_one()
        task = db.execute(select(BackupTask).where(BackupTask.id == record.task_id)).scalar_one()
        ds = db.execute(select(Datasource).where(Datasource.id == task.datasource_id)).scalar_one()

        _log("backup", record_id, "info", f"Starting {task.backup_type} backup", db)

        password = decrypt_password(ds.password)
        info = ConnectionInfo(
            host=ds.host, port=ds.port, username=ds.username,
            password=password, database=ds.database,
        )

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{ds.name}_{task.backup_type}_{timestamp}"
        storage_path = task.storage_path or settings.storage_path
        os.makedirs(storage_path, exist_ok=True)
        filepath = os.path.join(storage_path, filename)

        engine = _get_engine(ds.type)
        dump_file = engine.dump(info, filepath, task.compression)

        # Re-fetch record to check if cancelled during dump
        record = db.execute(select(BackupRecord).where(BackupRecord.id == record_id)).scalar_one()
        if record.status == "cancelled":
            if os.path.exists(dump_file):
                os.unlink(dump_file)
            _log("backup", record_id, "info", "Backup was cancelled during execution, file removed", db)
            return

        sha256 = hashlib.sha256()
        with open(dump_file, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        file_size = os.path.getsize(dump_file)

        record.status = "success"
        record.finished_at = datetime.datetime.utcnow()
        record.file_path = dump_file
        record.file_size = file_size
        record.checksum = sha256.hexdigest()
        db.commit()

        def _fmt(n: int) -> str:
            for u in ("B", "KB", "MB", "GB"):
                if n < 1024: return f"{n:.1f} {u}"
                n //= 1024
            return f"{n:.1f} TB"
        _log("backup", record_id, "info",
             f"Backup completed: {dump_file} ({_fmt(file_size)})", db)

    except Exception as e:
        record = db.execute(select(BackupRecord).where(BackupRecord.id == record_id)).scalar_one()
        record.status = "fail"
        record.finished_at = datetime.datetime.utcnow()
        err_msg = str(e)
        if isinstance(e, UnicodeDecodeError):
            err_msg = f"Backup process output decode error: {e.reason}"
        record.error_message = err_msg
        db.commit()
        _log("backup", record_id, "error", err_msg, db)
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="run_backup_scheduled")
def run_backup_scheduled(self, task_id: int):
    """Called by Celery Beat. Creates a BackupRecord then delegates to run_backup."""
    db = _sync_get_db()
    try:
        record = BackupRecord(task_id=task_id, status="running")
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id = record.id
    finally:
        db.close()
    run_backup.delay(record_id)


def _cron_match(parts: list[str]) -> bool:
    now = datetime.datetime.utcnow()
    minute, hour, day, month, week = parts
    if minute != "*" and now.minute != int(minute):
        return False
    if hour != "*" and now.hour != int(hour):
        return False
    if day != "*" and now.day != int(day):
        return False
    if month != "*" and now.month != int(month):
        return False
    if week != "*" and now.weekday() != int(week):
        return False
    return True


_last_run: dict[int, datetime.datetime] = {}


@celery_app.task(bind=True, name="check_schedules")
def check_schedules(self):
    """Runs every minute. Queries DB for enabled schedules and triggers due backups."""
    db = _sync_get_db()
    try:
        tasks = db.execute(
            select(BackupTask).where(
                BackupTask.is_enabled == True,
                BackupTask.schedule_config.isnot(None),
            )
        ).scalars().all()

        now = datetime.datetime.utcnow()
        for task in tasks:
            cron = task.schedule_config.get("cron") if task.schedule_config else None
            if not cron:
                continue
            parts = cron.split()
            if len(parts) != 5:
                continue

            last = _last_run.get(task.id)
            if last and (now - last).total_seconds() < 30:
                continue

            if _cron_match(parts):
                _last_run[task.id] = now
                run_backup_scheduled.delay(task.id)
    finally:
        db.close()
