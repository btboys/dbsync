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
from app.models import MigrationTask, MigrationRecord, Datasource, TaskLog
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


@celery_app.task(bind=True, name="run_migration")
def run_migration(self, record_id: int):
    db = _sync_get_db()
    try:
        record = db.execute(select(MigrationRecord).where(MigrationRecord.id == record_id)).scalar_one()
        task = db.execute(select(MigrationTask).where(MigrationTask.id == record.task_id)).scalar_one()
        src_ds = db.execute(select(Datasource).where(Datasource.id == task.source_datasource_id)).scalar_one()
        tgt_ds = db.execute(select(Datasource).where(Datasource.id == task.target_datasource_id)).scalar_one()

        db.add(TaskLog(task_type="migration", task_record_id=record_id, level="info",
                       message=f"Migration from {src_ds.name} to {tgt_ds.name} started"))
        db.commit()

        src_pwd = decrypt_password(src_ds.password)
        tgt_pwd = decrypt_password(tgt_ds.password)

        same_type = src_ds.type == tgt_ds.type
        total_rows = 0

        if task.transfer_type in ("schema_only", "schema_and_data"):
            _run_schema_transfer(src_ds, tgt_ds, src_pwd, tgt_pwd, same_type, record_id, db)

        if task.transfer_type in ("data_only", "schema_and_data"):
            rows = _run_data_migration(
                src_ds, tgt_ds, src_pwd, tgt_pwd,
                task.table_include, task.table_exclude, record_id, db,
            )
            total_rows += rows

        record.status = "success"
        record.finished_at = datetime.datetime.utcnow()
        record.rows_transferred = total_rows
        db.commit()

        db.add(TaskLog(task_type="migration", task_record_id=record_id, level="info",
                       message=f"Migration completed, {total_rows} rows transferred"))
        db.commit()

    except Exception as e:
        record = db.execute(select(MigrationRecord).where(MigrationRecord.id == record_id)).scalar_one()
        record.status = "fail"
        record.finished_at = datetime.datetime.utcnow()
        record.error_message = str(e)
        db.commit()
        db.add(TaskLog(task_type="migration", task_record_id=record_id, level="error", message=str(e)))
        db.commit()
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

    db.add(TaskLog(task_type="migration", task_record_id=record_id, level="info",
                   message=f"Schema transfer completed"))
    db.commit()


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
                        db.add(TaskLog(task_type="migration", task_record_id=record_id,
                                       level="warning", message=f"Schema stmt skip: {e}"))
                        db.commit()
        conn.commit()
    finally:
        conn.close()


def _run_data_migration(src_ds, tgt_ds, src_pwd, tgt_pwd,
                         include_tables, exclude_tables, record_id, db):
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
        for table in tables:
            try:
                src_cursor.execute(f"SELECT * FROM `{table}`" if src_ds.type == "mysql" else f'SELECT * FROM "{table}"')
            except Exception:
                continue
            rows = src_cursor.fetchall()
            if not rows:
                continue
            col_names = [desc[0] for desc in src_cursor.description]
            placeholders = ",".join(["%s"] * len(col_names))
            cols = ",".join(
                f"`{c}`" if tgt_ds.type == "mysql" else f'"{c}"' for c in col_names
            )
            for row in rows:
                try:
                    tgt_cursor.execute(
                        f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", row
                    )
                    total += 1
                except Exception as row_err:
                    db.add(TaskLog(task_type="migration", task_record_id=record_id,
                                   level="warning",
                                   message=f"Row skip {table}: {row_err}"))
                    db.commit()
            tgt_conn.commit()

        return total
    finally:
        src_conn.close()
        tgt_conn.close()
