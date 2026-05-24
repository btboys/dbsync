import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MigrationTaskCreate(BaseModel):
    name: str = Field(..., max_length=128)
    source_datasource_id: int
    target_datasource_id: int
    table_include: Optional[list[str]] = None
    table_exclude: Optional[list[str]] = None
    transfer_type: str = Field(..., pattern="^(schema_only|data_only|schema_and_data)$")


class MigrationTaskUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    source_datasource_id: Optional[int] = None
    target_datasource_id: Optional[int] = None
    table_include: Optional[list[str]] = None
    table_exclude: Optional[list[str]] = None
    transfer_type: Optional[str] = Field(None, pattern="^(schema_only|data_only|schema_and_data)$")


class MigrationTaskResponse(BaseModel):
    id: int
    name: str
    source_datasource_id: int
    target_datasource_id: int
    table_include: Optional[list[str]]
    table_exclude: Optional[list[str]]
    transfer_type: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class MigrationRecordResponse(BaseModel):
    id: int
    task_id: int
    status: str
    started_at: datetime.datetime
    finished_at: Optional[datetime.datetime]
    rows_transferred: Optional[int]
    error_message: Optional[str]

    model_config = {"from_attributes": True}
