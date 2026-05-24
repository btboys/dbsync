from typing import List, Optional, AsyncGenerator
import asyncio
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, select, desc
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models import TaskLog, TaskProcessLog, BackupRecord, BackupTask
from pydantic import BaseModel
import datetime
from sqlalchemy import func


def _sync_get_db():
    engine = create_engine(settings.database_url.replace("+aiomysql", "+pymysql"))
    return Session(engine)


class TaskLogResponse(BaseModel):
    id: int
    task_type: str
    task_record_id: int
    level: str
    message: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class TaskLogListResponse(BaseModel):
    items: List[TaskLogResponse]
    total: int


class RestoreRecordResponse(BaseModel):
    id: int
    task_record_id: int
    backup_name: str
    status: str
    message: str
    started_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]

    model_config = {"from_attributes": True}


class RestoreRecordListResponse(BaseModel):
    items: List[RestoreRecordResponse]
    total: int


router = APIRouter(prefix="/api/v1", tags=["logs"])


@router.get("/task-logs", response_model=TaskLogListResponse)
async def list_task_logs(
    task_type: Optional[str] = Query(None),
    task_record_id: Optional[int] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    q = select(TaskLog)
    if task_type:
        q = q.where(TaskLog.task_type == task_type)
    if task_record_id:
        q = q.where(TaskLog.task_record_id == task_record_id)
    if level:
        q = q.where(TaskLog.level == level)
    
    count_q = q.with_only_columns(TaskLog.id)
    count_result = await db.execute(count_q)
    total = len(count_result.scalars().all())
    
    q = q.order_by(desc(TaskLog.id)).offset(offset).limit(limit)
    result = await db.execute(q)
    items = result.scalars().all()
    return {"items": items, "total": total}


@router.get("/task-process-logs", response_model=TaskLogListResponse)
async def list_task_process_logs(
    task_type: Optional[str] = Query(None),
    task_record_id: Optional[int] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    q = select(TaskProcessLog)
    if task_type:
        q = q.where(TaskProcessLog.task_type == task_type)
    if task_record_id:
        q = q.where(TaskProcessLog.task_record_id == task_record_id)
    if level:
        q = q.where(TaskProcessLog.level == level)
    
    count_q = q.with_only_columns(TaskProcessLog.id)
    count_result = await db.execute(count_q)
    total = len(count_result.scalars().all())
    
    q = q.order_by(TaskProcessLog.id).offset(offset).limit(limit)
    result = await db.execute(q)
    items = result.scalars().all()
    return {"items": items, "total": total}


async def log_stream_generator(
    task_type: str,
    task_record_id: int,
    last_id: int,
) -> AsyncGenerator[str, None]:
    """SSE generator that polls DB for new logs and yields events."""
    current_last_id = last_id
    while True:
        await asyncio.sleep(1)
        db = _sync_get_db()
        try:
            q = (
                select(TaskLog)
                .where(TaskLog.task_type == task_type)
                .where(TaskLog.task_record_id == task_record_id)
                .where(TaskLog.id > current_last_id)
                .order_by(TaskLog.id)
            )
            result = db.execute(q)
            logs = result.scalars().all()
            for log in logs:
                data = {
                    "id": log.id,
                    "task_type": log.task_type,
                    "task_record_id": log.task_record_id,
                    "level": log.level,
                    "message": log.message,
                    "created_at": log.created_at.isoformat(),
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                current_last_id = log.id
        finally:
            db.close()


@router.get("/restore-records", response_model=RestoreRecordListResponse)
async def list_restore_records(
    limit: int = Query(200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate restore logs into restore records."""
    # Get all restore logs grouped by task_record_id
    q = (
        select(TaskLog.task_record_id, func.min(TaskLog.id).label("first_id"), func.max(TaskLog.id).label("last_id"))
        .where(TaskLog.task_type == "restore")
        .group_by(TaskLog.task_record_id)
        .order_by(desc(func.max(TaskLog.id)))
    )
    
    result = await db.execute(q)
    groups = result.all()
    total = len(groups)
    
    items = []
    for group in groups[offset:offset + limit]:
        task_record_id = group.task_record_id
        
        # Get first and last log for this restore
        first_log = await db.execute(
            select(TaskLog).where(TaskLog.id == group.first_id)
        )
        last_log = await db.execute(
            select(TaskLog).where(TaskLog.id == group.last_id)
        )
        first = first_log.scalar_one()
        last = last_log.scalar_one()
        
        # Determine status
        if last.level == "error":
            status = "fail"
            message = last.message
        elif "completed" in last.message.lower():
            status = "success"
            message = last.message
        else:
            status = "running"
            message = first.message
        
        # Get backup name
        backup_name = f"备份 #{task_record_id}"
        try:
            record = await db.execute(
                select(BackupRecord, BackupTask)
                .join(BackupTask, BackupRecord.task_id == BackupTask.id)
                .where(BackupRecord.id == task_record_id)
            )
            row = record.first()
            if row:
                backup_name = row.BackupTask.name
        except:
            pass
        
        items.append({
            "id": task_record_id,
            "task_record_id": task_record_id,
            "backup_name": backup_name,
            "status": status,
            "message": message,
            "started_at": first.created_at,
            "finished_at": last.created_at if status != "running" else None,
        })
    
    return {"items": items, "total": total}


@router.get("/task-logs/stream")
async def stream_task_logs(
    task_type: str = Query(...),
    task_record_id: int = Query(...),
    last_id: int = Query(0),
):
    """SSE endpoint for real-time task log streaming."""
    return StreamingResponse(
        log_stream_generator(task_type, task_record_id, last_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
