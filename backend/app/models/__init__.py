import datetime
from sqlalchemy import (
    Column, Integer, String, Text, BigInteger, Boolean, DateTime,
    ForeignKey, Enum, JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Datasource(Base):
    __tablename__ = "datasources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    type = Column(Enum("mysql", "postgresql", name="db_type"), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(64), nullable=False)
    password = Column(String(512), nullable=False)
    database = Column(String(64), nullable=False)
    ssl_config = Column(JSON, nullable=True)
    extra_params = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    backup_tasks = relationship("BackupTask", back_populates="datasource")
    source_migrations = relationship("MigrationTask", foreign_keys="MigrationTask.source_datasource_id", back_populates="source")
    target_migrations = relationship("MigrationTask", foreign_keys="MigrationTask.target_datasource_id", back_populates="target")


class BackupTask(Base):
    __tablename__ = "backup_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    datasource_id = Column(Integer, ForeignKey("datasources.id"), nullable=False)
    backup_type = Column(Enum("full", "incremental", name="backup_type"), nullable=False)
    schedule_config = Column(JSON, nullable=True)
    storage_path = Column(String(512))
    retention_days = Column(Integer, default=30)
    compression = Column(Boolean, default=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    datasource = relationship("Datasource", back_populates="backup_tasks")
    records = relationship("BackupRecord", back_populates="task")


class BackupRecord(Base):
    __tablename__ = "backup_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("backup_tasks.id"), nullable=False)
    status = Column(Enum("running", "success", "fail", "cancelled", name="record_status"), nullable=False, default="running")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    file_path = Column(String(512))
    file_size = Column(BigInteger)
    checksum = Column(String(64))
    error_message = Column(Text)
    incremental_base_id = Column(Integer, ForeignKey("backup_records.id"), nullable=True)

    task = relationship("BackupTask", back_populates="records")
    base_record = relationship("BackupRecord", remote_side=[id], backref="children")


class MigrationTask(Base):
    __tablename__ = "migration_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    source_datasource_id = Column(Integer, ForeignKey("datasources.id"), nullable=False)
    target_datasource_id = Column(Integer, ForeignKey("datasources.id"), nullable=False)
    table_include = Column(JSON, nullable=True)
    table_exclude = Column(JSON, nullable=True)
    transfer_type = Column(
        Enum("schema_only", "data_only", "schema_and_data", name="transfer_type"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    source = relationship("Datasource", foreign_keys=[source_datasource_id], back_populates="source_migrations")
    target = relationship("Datasource", foreign_keys=[target_datasource_id], back_populates="target_migrations")
    records = relationship("MigrationRecord", back_populates="task")


class MigrationRecord(Base):
    __tablename__ = "migration_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("migration_tasks.id"), nullable=False)
    status = Column(Enum("running", "success", "fail", "cancelled", name="migrate_status"), nullable=False, default="running")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    rows_transferred = Column(Integer)
    error_message = Column(Text)

    task = relationship("MigrationTask", back_populates="records")


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(Enum("backup", "migration", "restore", name="log_task_type"), nullable=False)
    task_record_id = Column(Integer, nullable=False)
    level = Column(Enum("info", "warning", "error", name="log_level"), nullable=False, default="info")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
