import datetime
import os
import subprocess
import tempfile

import psycopg2
import pymysql
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.config import settings
from app.core.security import decrypt_password
from app.models import MigrationTask, MigrationRecord, Datasource, TaskLog, TaskProcessLog
from app.worker.engines.base import ConnectionInfo


TYPE_MAP = {
    "mysql_to_postgresql": {
        "int": "INTEGER", "tinyint": "SMALLINT", "smallint": "SMALLINT",
        "bigint": "BIGINT", "varchar": "VARCHAR", "char": "CHAR",
        "text": "TEXT", "longtext": "TEXT", "mediumtext": "TEXT",
        "blob": "BYTEA", "longblob": "BYTEA", "mediumblob": "BYTEA",
        "double": "DOUBLE PRECISION", "float": "REAL", "decimal": "NUMERIC",
        "datetime": "TIMESTAMP", "timestamp": "TIMESTAMP", "date": "DATE",
        "time": "TIME", "tinyint(1)": "BOOLEAN",
    },
    "postgresql_to_mysql": {
        "integer": "INT", "bigint": "BIGINT", "smallint": "SMALLINT",
        "boolean": "TINYINT(1)", "text": "LONGTEXT", "character varying": "VARCHAR",
        "character": "CHAR", "timestamp": "DATETIME", "date": "DATE",
        "time": "TIME", "real": "FLOAT", "double precision": "DOUBLE",
        "numeric": "DECIMAL", "bytea": "LONGBLOB",
    },
}


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


def _log(task_type: str, record_id: int, level: str, msg: str, db: Session):
    db.add(TaskLog(task_type=task_type, task_record_id=record_id, level=level, message=msg))
    db.commit()


def _process_log(task_type: str, record_id: int, level: str, msg: str, db: Session):
    db.add(TaskProcessLog(task_type=task_type, task_record_id=record_id, level=level, message=msg))
    db.commit()


@celery_app.task(bind=True, name="run_migration")
def run_migration(self, record_id: int):
    db = _sync_get_db()
    try:
        record = db.execute(select(MigrationRecord).where(MigrationRecord.id == record_id)).scalar_one()
        task = db.execute(select(MigrationTask).where(MigrationTask.id == record.task_id)).scalar_one()
        src_ds = db.execute(select(Datasource).where(Datasource.id == task.source_datasource_id)).scalar_one()
        tgt_ds = db.execute(select(Datasource).where(Datasource.id == task.target_datasource_id)).scalar_one()

        _log("migration", record_id, "info", f"[开始] 从 {src_ds.name} 迁移到 {tgt_ds.name}", db)

        src_pwd = decrypt_password(src_ds.password)
        tgt_pwd = decrypt_password(tgt_ds.password)

        same_type = src_ds.type == tgt_ds.type
        total_rows = 0

        # 计算总步骤数
        steps = ["连接源数据库"]
        if task.transfer_type in ("schema_only", "schema_and_data"):
            steps.append("传输表结构")
        if task.transfer_type in ("data_only", "schema_and_data"):
            steps.append("迁移数据")
        total_steps = len(steps)

        step = 1
        _process_log("migration", record_id, "info",
                     f"[步骤 {step}/{total_steps}] 连接源数据库: {src_ds.host}:{src_ds.port}/{src_ds.database}", db)

        if task.transfer_type in ("schema_only", "schema_and_data"):
            step += 1
            _process_log("migration", record_id, "info", f"[步骤 {step}/{total_steps}] 传输表结构", db)
            _run_schema_transfer(src_ds, tgt_ds, src_pwd, tgt_pwd, same_type, record_id, db)

        if task.transfer_type in ("data_only", "schema_and_data"):
            step += 1
            _process_log("migration", record_id, "info", f"[步骤 {step}/{total_steps}] 迁移数据", db)
            rows = _run_data_migration(
                src_ds, tgt_ds, src_pwd, tgt_pwd,
                task.table_include, task.table_exclude, record_id, db,
            )
            total_rows += rows

        record.status = "success"
        record.finished_at = datetime.datetime.utcnow()
        record.rows_transferred = total_rows
        db.commit()

        _log("migration", record_id, "info", f"Migration completed, {total_rows} rows transferred", db)

    except Exception as e:
        record = db.execute(select(MigrationRecord).where(MigrationRecord.id == record_id)).scalar_one()
        record.status = "fail"
        record.finished_at = datetime.datetime.utcnow()
        record.error_message = str(e)
        db.commit()
        _log("migration", record_id, "error", str(e), db)
        raise
    finally:
        db.close()


def _run_schema_transfer(src_ds, tgt_ds, src_pwd, tgt_pwd, same_type, record_id, db):
    engine = _get_engine(src_ds.type)
    tmp_path = f"/tmp/migrate_schema_{record_id}.sql"
    info = ConnectionInfo(
        host=src_ds.host, port=src_ds.port, username=src_ds.username,
        password=src_pwd, database=src_ds.database,
    )
    cmd = engine.transfer_schema_cmd(info, tmp_path)
    subprocess.run(cmd, check=True, timeout=300)

    if same_type:
        tgt_engine = _get_engine(tgt_ds.type)
        tgt_info = ConnectionInfo(
            host=tgt_ds.host, port=tgt_ds.port, username=tgt_ds.username,
            password=tgt_pwd, database=tgt_ds.database,
        )
        subprocess.run(tgt_engine.restore_cmd(tgt_info, tmp_path), check=True, timeout=300)
    else:
        _run_cross_schema_apply(tmp_path, tgt_ds, tgt_pwd, src_ds.type, tgt_ds.type, record_id, db)

    _log("migration", record_id, "info", "Schema transfer completed", db)


def _run_cross_schema_apply(schema_path, tgt_ds, tgt_pwd, src_type, tgt_type, record_id, db):
    with open(schema_path) as f:
        sql_content = f.read()
    key = f"{src_type}_to_{tgt_type}"
    mapping = TYPE_MAP.get(key, {})
    for src_t, tgt_t in mapping.items():
        sql_content = sql_content.replace(src_t, tgt_t)

    if tgt_ds.type == "mysql":
        conn = pymysql.connect(
            host=tgt_ds.host, port=tgt_ds.port, user=tgt_ds.username,
            password=tgt_pwd, database=tgt_ds.database,
        )
    else:
        conn = psycopg2.connect(
            host=tgt_ds.host, port=tgt_ds.port, user=tgt_ds.username,
            password=tgt_pwd, dbname=tgt_ds.database,
        )
    try:
        with conn.cursor() as cur:
            for stmt in sql_content.split(";"):
                stmt = stmt.strip()
                if stmt:
                    try:
                        cur.execute(stmt)
                    except Exception as e:
                        _process_log("migration", record_id, "warning", f"Schema stmt skip: {e}", db)
        conn.commit()
    finally:
        conn.close()


def _run_data_migration(src_ds, tgt_ds, src_pwd, tgt_pwd,
                         include_tables, exclude_tables, record_id, db):
    BATCH_SIZE = 1000

    if src_ds.type == "mysql":
        src_conn = pymysql.connect(
            host=src_ds.host, port=src_ds.port, user=src_ds.username,
            password=src_pwd, database=src_ds.database,
        )
    else:
        src_conn = psycopg2.connect(
            host=src_ds.host, port=src_ds.port, user=src_ds.username,
            password=src_pwd, dbname=src_ds.database,
        )

    if tgt_ds.type == "mysql":
        tgt_conn = pymysql.connect(
            host=tgt_ds.host, port=tgt_ds.port, user=tgt_ds.username,
            password=tgt_pwd, database=tgt_ds.database,
        )
    else:
        tgt_conn = psycopg2.connect(
            host=tgt_ds.host, port=tgt_ds.port, user=tgt_ds.username,
            password=tgt_pwd, dbname=tgt_ds.database,
        )

    try:
        src_cursor = src_conn.cursor()
        tgt_cursor = tgt_conn.cursor()

        if src_ds.type == "mysql":
            src_cursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'"
            )
        else:
            src_cursor.execute(
                "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
            )
        all_tables = [r[0] for r in src_cursor.fetchall()]

        if include_tables:
            tables = [t for t in all_tables if t in include_tables]
        elif exclude_tables:
            tables = [t for t in all_tables if t not in exclude_tables]
        else:
            tables = all_tables

        total = 0
        table_count = len(tables)
        for idx, table in enumerate(tables, 1):
            _process_log("migration", record_id, "info", f"[进度] 正在迁移表 {table} ({idx}/{table_count})", db)
            try:
                src_cursor.execute(f"SELECT * FROM `{table}`" if src_ds.type == "mysql" else f'SELECT * FROM "{table}"')
            except Exception:
                _process_log("migration", record_id, "warning", f"跳过表 {table}: 查询失败", db)
                continue

            col_names = [desc[0] for desc in src_cursor.description]
            placeholders = ",".join(["%s"] * len(col_names))
            cols = ",".join(
                f"`{c}`" if tgt_ds.type == "mysql" else f'"{c}"' for c in col_names
            )
            insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

            table_rows = 0
            batch = []
            while True:
                rows = src_cursor.fetchmany(BATCH_SIZE)
                if not rows:
                    break
                batch.extend(rows)

                if len(batch) >= BATCH_SIZE:
                    try:
                        tgt_cursor.executemany(insert_sql, batch)
                        total += len(batch)
                        table_rows += len(batch)
                    except Exception as err:
                        _process_log("migration", record_id, "warning", f"批量插入失败 {table}: {err}，回退到逐行插入", db)
                        for row in batch:
                            try:
                                tgt_cursor.execute(insert_sql, row)
                                total += 1
                                table_rows += 1
                            except Exception as row_err:
                                _process_log("migration", record_id, "warning", f"跳过行 {table}: {row_err}", db)
                    batch = []
                    tgt_conn.commit()

            if batch:
                try:
                    tgt_cursor.executemany(insert_sql, batch)
                    total += len(batch)
                    table_rows += len(batch)
                except Exception as err:
                    _process_log("migration", record_id, "warning", f"批量插入失败 {table}: {err}，回退到逐行插入", db)
                    for row in batch:
                        try:
                            tgt_cursor.execute(insert_sql, row)
                            total += 1
                            table_rows += 1
                        except Exception as row_err:
                            _process_log("migration", record_id, "warning", f"跳过行 {table}: {row_err}", db)
                tgt_conn.commit()

            if table_rows == 0:
                _process_log("migration", record_id, "info", f"表 {table} 为空，跳过", db)
            else:
                _process_log("migration", record_id, "info", f"表 {table} 完成，迁移 {table_rows} 行", db)

        return total
    finally:
        src_conn.close()
        tgt_conn.close()
