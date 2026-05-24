from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.celery_app import celery_app
from app.models import MigrationTask, MigrationRecord
from app.schemas.migration import (
    MigrationTaskCreate, MigrationTaskUpdate, MigrationTaskResponse, MigrationRecordResponse,
)

router = APIRouter(prefix="/api/v1", tags=["migration"])


@router.get("/migration-tasks", response_model=List[MigrationTaskResponse])
async def list_migration_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MigrationTask).order_by(MigrationTask.id))
    return result.scalars().all()


@router.get("/migration-tasks/{task_id}", response_model=MigrationTaskResponse)
async def get_migration_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MigrationTask).where(MigrationTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Migration task not found")
    return task


@router.post("/migration-tasks", response_model=MigrationTaskResponse, status_code=201)
async def create_migration_task(body: MigrationTaskCreate, db: AsyncSession = Depends(get_db)):
    task = MigrationTask(**body.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/migration-tasks/{task_id}", response_model=MigrationTaskResponse)
async def update_migration_task(task_id: int, body: MigrationTaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MigrationTask).where(MigrationTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Migration task not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/migration-tasks/{task_id}", status_code=204)
async def delete_migration_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MigrationTask).where(MigrationTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Migration task not found")
    await db.delete(task)
    await db.commit()


@router.post("/migration-tasks/{task_id}/run")
async def run_migration_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MigrationTask).where(MigrationTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Migration task not found")

    record = MigrationRecord(task_id=task_id, status="running")
    db.add(record)
    await db.commit()
    await db.refresh(record)

    celery_app.send_task("run_migration", args=[record.id])
    return {"record_id": record.id, "status": "started"}


@router.get("/migration-records", response_model=List[MigrationRecordResponse])
async def list_migration_records(
    task_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(MigrationRecord)
    if task_id:
        q = q.where(MigrationRecord.task_id == task_id)
    if status:
        q = q.where(MigrationRecord.status == status)
    q = q.order_by(desc(MigrationRecord.id))
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/migration-records/{record_id}/cancel")
async def cancel_migration_record(record_id: int, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    from app.models import TaskLog

    result = await db.execute(select(MigrationRecord).where(MigrationRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "Migration record not found")
    if record.status != "running":
        raise HTTPException(400, "Only running records can be cancelled")

    record.status = "cancelled"
    record.finished_at = datetime.utcnow()

    db.add(TaskLog(
        task_type="migration",
        task_record_id=record_id,
        level="info",
        message="Migration cancelled by user",
    ))
    await db.commit()
    return {"record_id": record_id, "status": "cancelled"}
