from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.lead import Lead, LeadStatus, LeadSource
from backend.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from backend.schemas.common import BaseResponse, ListResponse
from backend.crud.lead import LeadCRUD

router = APIRouter()


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    obj_in: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = await LeadCRUD.create(db, obj_in, organization_id=current_user.organization_id)
    return lead


@router.get("/", response_model=ListResponse[LeadResponse])
async def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[LeadStatus] = None,
    source: Optional[LeadSource] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    leads, total = await LeadCRUD.get_list(
        db, skip=skip, limit=limit,
        status=status, source=source, search=search,
        organization_id=current_user.organization_id,
    )
    return ListResponse(
        data=leads,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = await LeadCRUD.get(db, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="潜客不存在")
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    obj_in: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = await LeadCRUD.get(db, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="潜客不存在")
    lead = await LeadCRUD.update(db, lead, obj_in)
    return lead


@router.delete("/{lead_id}", response_model=BaseResponse)
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = await LeadCRUD.get(db, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="潜客不存在")
    await LeadCRUD.delete(db, lead)
    return BaseResponse(message="删除成功")
