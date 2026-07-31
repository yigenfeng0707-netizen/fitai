from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.campaign import CampaignStatus
from backend.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from backend.schemas.common import ListResponse
from backend.crud.campaign import CampaignCRUD

router = APIRouter()


@router.get("/", response_model=ListResponse[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[CampaignStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await CampaignCRUD.get_list(
        db, organization_id=current_user.organization_id,
        skip=skip, limit=limit, status=status,
    )
    return ListResponse(
        data=items, total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    obj_in: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CampaignCRUD.create(
        db, obj_in, organization_id=current_user.organization_id,
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await CampaignCRUD.get(
        db, campaign_id, organization_id=current_user.organization_id,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found",
        )
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    obj_in: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await CampaignCRUD.get(
        db, campaign_id, organization_id=current_user.organization_id,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found",
        )
    return await CampaignCRUD.update(db, campaign, obj_in)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await CampaignCRUD.get(
        db, campaign_id, organization_id=current_user.organization_id,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found",
        )
    await CampaignCRUD.delete(db, campaign)
