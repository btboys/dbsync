import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BackupTaskCreate(BaseModel):
    name: str = Field(..., max_length=128)
    datasource_id: int
    backup_type: str = Field(..., pattern="^(full|incremental)$")
    schedule_config: Optional[dict] = None
    storage_path: Optional[str] = None
    retention_days: int = 30
    compression: bool = True
    is_enabled: bool = True


class BackupTaskUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    schedule_config: Optional[dict] = None
    storage_path: Optional[str] = None
    retention_days: Optional[int] = None
    compression: Optional[bool] = None
    is_enabled: Optional[bool] = None


class BackupTaskResponse(BaseModel):
    id: int
    name: str
    datasource_id: int
    backup_type: str
    schedule_config: Optional[dict]
    storage_path: Optional[str]
    retention_days: int
    compression: bool
    is_enabled: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class BackupRecordResponse(BaseModel):
    id: int
    task_id: int
    status: str
    started_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]
    file_path: Optional[str]
    file_size: Optional[int]
    uncompressed_size: Optional[int]
    checksum: Optional[str]
    error_message: Optional[str]

    model_config = {"from_attributes": True}


class RestoreRequest(BaseModel):
    target_datasource_id: Optional[int] = None
    target_host: Optional[str] = None
    target_port: Optional[int] = None
    target_username: Optional[str] = None
    target_password: Optional[str] = None
    target_database: Optional[str] = None
    target_db_type: Optional[str] = Field(None, pattern="^(mysql|postgresql)$")
