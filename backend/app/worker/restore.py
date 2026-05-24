import subprocess

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.config import settings
from app.core.security import decrypt_password
from app.models import BackupRecord, BackupTask, Datasource, TaskLog, TaskProcessLog
from app.worker.engines.base import ConnectionInfo


def _sync_get_db():
    engine = create_engine(settings.database_url.replace("+aiomysql", "+pymysql"))
    return Session(engine)


def _process_log(task_type: str, record_id: int, level: str, msg: str, db: Session):
    db.add(TaskProcessLog(task_type=task_type, task_record_id=record_id, level=level, message=msg))
    db.commit()


def _get_engine(db_type: str):
    from app.worker.engines.mysql import MySQLEngine
    from app.worker.engines.postgresql import PostgreSQLEngine
    if db_type == "mysql":
        return MySQLEngine()
    elif db_type == "postgresql":
        return PostgreSQLEngine()
    raise ValueError(f"Unsupported database type: {db_type}")


@celery_app.task(bind=True, name="run_restore")
def run_restore(self, record_id: int, target: dict = None):
    db = _sync_get_db()
    try:
        record = db.execute(select(BackupRecord).where(BackupRecord.id == record_id)).scalar_one()
        task = db.execute(select(BackupTask).where(BackupTask.id == record.task_id)).scalar_one()
        ds = db.execute(select(Datasource).where(Datasource.id == task.datasource_id)).scalar_one()

        db.add(TaskLog(task_type="restore", task_record_id=record_id, level="info",
                       message=f"Starting restore from {record.file_path}"))
        db.commit()

        # Use target connection if provided
        if target and target.get("target_datasource_id"):
            target_ds = db.execute(select(Datasource).where(Datasource.id == target["target_datasource_id"])).scalar_one()
            target_password = decrypt_password(target_ds.password)
            info = ConnectionInfo(
                host=target_ds.host, port=target_ds.port, username=target_ds.username,
                password=target_password, database=target_ds.database,
            )
            db_type = target_ds.type
            target_name = f"{target_ds.host}:{target_ds.port}/{target_ds.database}"
        elif target and target.get("target_host"):
            info = ConnectionInfo(
                host=target["target_host"],
                port=target.get("target_port", 3306),
                username=target["target_username"],
                password=target["target_password"],
                database=target["target_database"],
            )
            db_type = target.get("target_db_type", "mysql")
            target_name = f"{info.host}:{info.port}/{info.database}"
        else:
            password = decrypt_password(ds.password)
            info = ConnectionInfo(
                host=ds.host, port=ds.port, username=ds.username,
                password=password, database=ds.database,
            )
            db_type = ds.type
            target_name = f"{ds.host}:{ds.port}/{ds.database}"

        _process_log("restore", record_id, "info", f"[步骤 1/3] 连接目标数据库: {target_name}", db)

        engine = _get_engine(db_type)
        cmd = engine.restore_cmd(info, record.file_path)
        _process_log("restore", record_id, "info", f"[步骤 2/3] 执行恢复命令...", db)

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        stdout, stderr = process.communicate(timeout=3600)

        if stdout:
            _process_log("restore", record_id, "info", f"命令输出: {stdout[:500]}", db)
        if stderr:
            _process_log("restore", record_id, "warning", f"命令警告: {stderr[:500]}", db)

        if process.returncode != 0:
            raise RuntimeError(stderr.strip() or f"Restore failed with code {process.returncode}")

        _process_log("restore", record_id, "info", f"[步骤 3/3] 恢复完成", db)
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
