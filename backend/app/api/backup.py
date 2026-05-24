from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.celery_app import celery_app
from app.models import BackupTask, BackupRecord
from app.schemas.backup import (
    BackupTaskCreate, BackupTaskUpdate, BackupTaskResponse,
    BackupRecordResponse,
)

router = APIRouter(prefix="/api/v1", tags=["backup"])


@router.get("/backup-tasks", response_model=List[BackupTaskResponse])
async def list_backup_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackupTask).order_by(BackupTask.id))
    return result.scalars().all()


@router.get("/backup-tasks/{task_id}", response_model=BackupTaskResponse)
async def get_backup_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Backup task not found")
    return task


@router.post("/backup-tasks", response_model=BackupTaskResponse, status_code=201)
async def create_backup_task(body: BackupTaskCreate, db: AsyncSession = Depends(get_db)):
    task = BackupTask(**body.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/backup-tasks/{task_id}", response_model=BackupTaskResponse)
async def update_backup_task(task_id: int, body: BackupTaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Backup task not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/backup-tasks/{task_id}", status_code=204)
async def delete_backup_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Backup task not found")
    await db.delete(task)
    await db.commit()


@router.post("/backup-tasks/{task_id}/run")
async def run_backup_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackupTask).where(BackupTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Backup task not found")

    record = BackupRecord(task_id=task_id, status="running")
    db.add(record)
    await db.commit()
    await db.refresh(record)

    celery_app.send_task("run_backup", args=[record.id])
    return {"record_id": record.id, "status": "started"}


@router.get("/backup-records", response_model=List[BackupRecordResponse])
async def list_backup_records(
    task_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(BackupRecord).order_by(desc(BackupRecord.id))
    if task_id:
        q = q.where(BackupRecord.task_id == task_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/backup-records/{record_id}", response_model=BackupRecordResponse)
async def get_backup_record(record_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackupRecord).where(BackupRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "Backup record not found")
    return record


@router.post("/backup-records/{record_id}/restore")
async def restore_backup(record_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackupRecord).where(BackupRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "Backup record not found")

    celery_app.send_task("run_restore", args=[record_id])
    return {"record_id": record_id, "status": "restore_started"}
