from typing import List, Optional, AsyncGenerator
import asyncio
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import TaskLog
from pydantic import BaseModel
import datetime


class TaskLogResponse(BaseModel):
    id: int
    task_type: str
    task_record_id: int
    level: str
    message: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/api/v1", tags=["logs"])


@router.get("/task-logs", response_model=List[TaskLogResponse])
async def list_task_logs(
    task_type: Optional[str] = Query(None),
    task_record_id: Optional[int] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(200),
    db: AsyncSession = Depends(get_db),
):
    q = select(TaskLog).order_by(desc(TaskLog.id)).limit(limit)
    if task_type:
        q = q.where(TaskLog.task_type == task_type)
    if task_record_id:
        q = q.where(TaskLog.task_record_id == task_record_id)
    if level:
        q = q.where(TaskLog.level == level)
    result = await db.execute(q)
    return result.scalars().all()


async def log_stream_generator(
    task_type: str,
    task_record_id: int,
    last_id: int,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """SSE generator that polls DB for new logs and yields events."""
    current_last_id = last_id
    while True:
        await asyncio.sleep(1)
        q = (
            select(TaskLog)
            .where(TaskLog.task_type == task_type)
            .where(TaskLog.task_record_id == task_record_id)
            .where(TaskLog.id > current_last_id)
            .order_by(TaskLog.id)
        )
        result = await db.execute(q)
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


@router.get("/task-logs/stream")
async def stream_task_logs(
    task_type: str = Query(...),
    task_record_id: int = Query(...),
    last_id: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint for real-time task log streaming."""
    return StreamingResponse(
        log_stream_generator(task_type, task_record_id, last_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
