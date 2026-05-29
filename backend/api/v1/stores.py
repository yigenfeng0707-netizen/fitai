"""API - 门店管理"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.schemas.store import (
    StoreCreate, StoreUpdate, StoreResponse, StoreListResponse,
    StoreStaffAssign,
)
from backend.schemas.common import ListResponse
from backend.crud.store import StoreCRUD

router = APIRouter()


@router.post("/", response_model=StoreResponse, status_code=201)
async def create_store(
    obj_in: StoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = await StoreCRUD.create(db, obj_in, organization_id=current_user.organization_id)
    return store


@router.get("/", response_model=ListResponse[StoreListResponse])
async def list_stores(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stores, total = await StoreCRUD.get_multi(
        db, organization_id=current_user.organization_id,
        skip=skip, limit=limit, is_active=is_active,
    )
    return ListResponse(data=stores, total=total, page=skip // limit + 1, page_size=limit)


@router.get("/my/", response_model=list[StoreResponse])
async def get_my_stores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stores = await StoreCRUD.get_staff_stores(db, current_user.id, current_user.organization_id)
    return stores


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = await StoreCRUD.get(db, store_id, organization_id=current_user.organization_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    return store


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: int,
    obj_in: StoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = await StoreCRUD.get(db, store_id, organization_id=current_user.organization_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    store = await StoreCRUD.update(db, store, obj_in)
    return store


@router.delete("/{store_id}")
async def delete_store(
    store_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = await StoreCRUD.get(db, store_id, organization_id=current_user.organization_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    await StoreCRUD.delete(db, store)
    return {"success": True, "message": "删除成功"}


@router.get("/{store_id}/staff/", response_model=list[dict])
async def get_store_staff(
    store_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = await StoreCRUD.get(db, store_id, organization_id=current_user.organization_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    staff = await StoreCRUD.get_staff(db, store_id, current_user.organization_id)
    return staff


@router.post("/{store_id}/staff/", status_code=201)
async def assign_staff(
    store_id: int,
    obj_in: StoreStaffAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = await StoreCRUD.get(db, store_id, organization_id=current_user.organization_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    us = await StoreCRUD.assign_staff(
        db, store_id, obj_in.user_id,
        role_at_store=obj_in.role_at_store,
        is_primary=obj_in.is_primary,
        organization_id=current_user.organization_id,
    )
    return {"success": True, "message": "分配成功"}


@router.delete("/{store_id}/staff/{user_id}")
async def remove_staff(
    store_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = await StoreCRUD.get(db, store_id, organization_id=current_user.organization_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    await StoreCRUD.remove_staff(db, store_id, user_id, current_user.organization_id)
    return {"success": True, "message": "移除成功"}


@router.post("/{store_id}/staff/{user_id}/primary")
async def set_primary_store(
    store_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = await StoreCRUD.get(db, store_id, organization_id=current_user.organization_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    await StoreCRUD.set_primary_store(db, user_id, store_id, current_user.organization_id)
    return {"success": True, "message": "设置成功"}
