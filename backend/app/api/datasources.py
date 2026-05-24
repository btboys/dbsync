from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import encrypt_password, decrypt_password
from app.models import Datasource
from app.schemas.datasource import (
    DatasourceCreate, DatasourceUpdate, DatasourceResponse, DatasourceListResponse,
)

router = APIRouter(prefix="/api/v1/datasources", tags=["datasources"])


@router.get("", response_model=List[DatasourceListResponse])
async def list_datasources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Datasource).order_by(Datasource.id))
    return result.scalars().all()


@router.get("/{ds_id}", response_model=DatasourceResponse)
async def get_datasource(ds_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Datasource).where(Datasource.id == ds_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(404, "Datasource not found")
    return ds


@router.post("", response_model=DatasourceResponse, status_code=201)
async def create_datasource(body: DatasourceCreate, db: AsyncSession = Depends(get_db)):
    ds = Datasource(**body.model_dump(exclude={"password"}))
    ds.password = encrypt_password(body.password)
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    return ds


@router.put("/{ds_id}", response_model=DatasourceResponse)
async def update_datasource(ds_id: int, body: DatasourceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Datasource).where(Datasource.id == ds_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(404, "Datasource not found")
    update_data = body.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = encrypt_password(update_data["password"])
    for k, v in update_data.items():
        setattr(ds, k, v)
    await db.commit()
    await db.refresh(ds)
    return ds


@router.delete("/{ds_id}", status_code=204)
async def delete_datasource(ds_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Datasource).where(Datasource.id == ds_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(404, "Datasource not found")
    await db.delete(ds)
    await db.commit()


@router.post("/{ds_id}/test")
async def test_datasource(ds_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Datasource).where(Datasource.id == ds_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(404, "Datasource not found")

    import asyncio
    password = decrypt_password(ds.password)

    try:
        if ds.type == "mysql":
            import aiomysql
            conn = await asyncio.wait_for(
                aiomysql.connect(
                    host=ds.host, port=ds.port, user=ds.username,
                    password=password, db=ds.database, connect_timeout=5,
                ),
                timeout=10,
            )
            conn.close()
        elif ds.type == "postgresql":
            import asyncpg
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=ds.host, port=ds.port, user=ds.username,
                    password=password, database=ds.database, timeout=5,
                ),
                timeout=10,
            )
            await conn.close()
        return {"status": "ok", "message": "Connection successful"}
    except Exception as e:
        raise HTTPException(400, detail=f"Connection failed: {str(e)}")
