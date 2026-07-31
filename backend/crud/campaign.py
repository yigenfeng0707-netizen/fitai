from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.campaign import Campaign, CampaignStatus
from backend.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignCRUD:
    @staticmethod
    async def create(
        db: AsyncSession, obj_in: CampaignCreate, organization_id: int,
    ) -> Campaign:
        campaign = Campaign(
            name=obj_in.name,
            description=obj_in.description,
            campaign_type=obj_in.campaign_type,
            channels=obj_in.channels,
            target_audience=obj_in.target_audience,
            target_count=obj_in.target_count,
            budget=obj_in.budget,
            start_date=obj_in.start_date,
            end_date=obj_in.end_date,
            organization_id=organization_id,
        )
        db.add(campaign)
        await db.flush()
        return campaign

    @staticmethod
    async def get(
        db: AsyncSession, campaign_id: int, organization_id: int,
    ) -> Optional[Campaign]:
        result = await db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, campaign: Campaign, obj_in: CampaignUpdate) -> Campaign:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        await db.flush()
        return campaign

    @staticmethod
    async def delete(db: AsyncSession, campaign: Campaign) -> None:
        await db.delete(campaign)

    @staticmethod
    async def get_list(
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[CampaignStatus] = None,
    ) -> tuple[list[Campaign], int]:
        query = select(Campaign).where(
            Campaign.organization_id == organization_id,
        )
        if status:
            query = query.where(Campaign.status == status)
        total_result = await db.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total = total_result.scalar()
        result = await db.execute(
            query.order_by(Campaign.created_at.desc())
            .offset(skip).limit(limit),
        )
        return list(result.scalars().all()), total or 0
