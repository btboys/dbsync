import datetime
import hashlib
import os
import subprocess

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.config import settings
from app.core.security import decrypt_password
from app.models import BackupTask, BackupRecord, TaskLog, Datasource
from app.worker.engines import get_engine
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
        ext = ".sql.gz" if task.compression else ".sql"
        filename = f"{ds.name}_{task.backup_type}_{timestamp}{ext}"
        storage_path = task.storage_path or settings.storage_path
        os.makedirs(storage_path, exist_ok=True)
        filepath = os.path.join(storage_path, filename)

        engine = _get_engine(ds.type)
        cmd = engine.dump_cmd(info, filepath, task.compression)

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        stdout, stderr = process.communicate(timeout=3600)

        if process.returncode != 0:
            raise RuntimeError(stderr.strip() or f"Process exited with code {process.returncode}")

        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        file_size = os.path.getsize(filepath)

        record.status = "success"
        record.finished_at = datetime.datetime.utcnow()
        record.file_path = filepath
        record.file_size = file_size
        record.checksum = sha256.hexdigest()
        db.commit()

        _log("backup", record_id, "info",
             f"Backup completed: {filepath} ({file_size} bytes)", db)

    except Exception as e:
        record = db.execute(select(BackupRecord).where(BackupRecord.id == record_id)).scalar_one()
        record.status = "fail"
        record.finished_at = datetime.datetime.utcnow()
        record.error_message = str(e)
        db.commit()
        _log("backup", record_id, "error", str(e), db)
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
