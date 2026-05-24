import subprocess

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.config import settings
from app.core.security import decrypt_password
from app.models import BackupRecord, BackupTask, Datasource, TaskLog
from app.worker.engines.base import ConnectionInfo


def _sync_get_db():
    engine = create_engine(settings.database_url.replace("+aiomysql", "+pymysql"))
    return Session(engine)


def _get_engine(db_type: str):
    from app.worker.engines.mysql import MySQLEngine
    from app.worker.engines.postgresql import PostgreSQLEngine
    if db_type == "mysql":
        return MySQLEngine()
    elif db_type == "postgresql":
        return PostgreSQLEngine()
    raise ValueError(f"Unsupported database type: {db_type}")


@celery_app.task(bind=True, name="run_restore")
def run_restore(self, record_id: int):
    db = _sync_get_db()
    try:
        record = db.execute(select(BackupRecord).where(BackupRecord.id == record_id)).scalar_one()
        task = db.execute(select(BackupTask).where(BackupTask.id == record.task_id)).scalar_one()
        ds = db.execute(select(Datasource).where(Datasource.id == task.datasource_id)).scalar_one()

        db.add(TaskLog(task_type="restore", task_record_id=record_id, level="info",
                       message=f"Starting restore from {record.file_path}"))
        db.commit()

        password = decrypt_password(ds.password)
        info = ConnectionInfo(
            host=ds.host, port=ds.port, username=ds.username,
            password=password, database=ds.database,
        )

        engine = _get_engine(ds.type)
        cmd = engine.restore_cmd(info, record.file_path)

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        stdout, stderr = process.communicate(timeout=3600)

        if process.returncode != 0:
            raise RuntimeError(stderr.strip() or f"Restore failed with code {process.returncode}")

        db.add(TaskLog(task_type="restore", task_record_id=record_id, level="info",
                       message="Restore completed successfully"))
        db.commit()

    except Exception as e:
        db.add(TaskLog(task_type="restore", task_record_id=record_id, level="error",
                       message=str(e)))
        db.commit()
        raise
    finally:
        db.close()
