from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.lead import Lead, LeadStatus, LeadSource, LeadIntent
from backend.schemas.lead import LeadCreate, LeadUpdate


class LeadCRUD:
    @staticmethod
    async def get(db: AsyncSession, lead_id: int) -> Optional[Lead]:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, obj_in: LeadCreate, organization_id: int = 1) -> Lead:
        lead = Lead(**obj_in.model_dump(), organization_id=organization_id)
        db.add(lead)
        await db.flush()
        return lead

    @staticmethod
    async def update(db: AsyncSession, lead: Lead, obj_in: LeadUpdate) -> Lead:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)
        await db.flush()
        return lead

    @staticmethod
    async def delete(db: AsyncSession, lead: Lead) -> None:
        await db.delete(lead)

    @staticmethod
    async def get_list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        search: Optional[str] = None,
        organization_id: int = 1,
    ) -> tuple[list[Lead], int]:
        query = select(Lead).where(Lead.organization_id == organization_id)

        if status:
            query = query.where(Lead.status == status)
        if source:
            query = query.where(Lead.source == source)
        if search:
            query = query.where(
                (Lead.name.ilike(f"%{search}%")) |
                (Lead.phone.ilike(f"%{search}%"))
            )

        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar() or 0

        query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)

        return list(result.scalars().all()), total
