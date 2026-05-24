import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DatasourceCreate(BaseModel):
    name: str = Field(..., max_length=64)
    type: str = Field(..., pattern="^(mysql|postgresql)$")
    host: str = Field(..., max_length=255)
    port: int
    username: str = Field(..., max_length=64)
    password: str = Field(..., max_length=512)
    database: str = Field(..., max_length=64)
    ssl_config: Optional[dict] = None
    extra_params: Optional[dict] = None
    is_active: bool = True


class DatasourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = None
    username: Optional[str] = Field(None, max_length=64)
    password: Optional[str] = Field(None, max_length=512)
    database: Optional[str] = Field(None, max_length=64)
    ssl_config: Optional[dict] = None
    extra_params: Optional[dict] = None
    is_active: Optional[bool] = None


class DatasourceResponse(BaseModel):
    id: int
    name: str
    type: str
    host: str
    port: int
    username: str
    password: str = Field(exclude=True)
    database: str
    ssl_config: Optional[dict]
    extra_params: Optional[dict]
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class DatasourceListResponse(BaseModel):
    id: int
    name: str
    type: str
    host: str
    port: int
    username: str
    database: str
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
