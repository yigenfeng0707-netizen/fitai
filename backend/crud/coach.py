"""
CRUD - 教练
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.coach import Coach
from backend.schemas.coach import CoachCreate, CoachUpdate


class CoachCRUD:
    """教练 CRUD"""
    
    @staticmethod
    async def get(db: AsyncSession, coach_id: int) -> Optional[Coach]:
        """获取教练"""
        result = await db.execute(
            select(Coach).where(Coach.id == coach_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[Coach]:
        """通过手机号获取教练"""
        result = await db.execute(
            select(Coach).where(Coach.phone == phone)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: CoachCreate, organization_id: int = 1) -> Coach:
        """创建教练"""
        coach = Coach(
            name=obj_in.name,
            phone=obj_in.phone,
            email=obj_in.email,
            specialization=obj_in.specialization,
            introduction=obj_in.introduction,
            certificates=obj_in.certificates,
            work_schedule=obj_in.work_schedule,
            is_active=obj_in.is_active,
            organization_id=organization_id,
        )
        
        db.add(coach)
        await db.flush()
        return coach
    
    @staticmethod
    async def update(db: AsyncSession, coach: Coach, obj_in: CoachUpdate) -> Coach:
        """更新教练"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(coach, field, value)
        
        await db.flush()
        return coach
    
    @staticmethod
    async def delete(db: AsyncSession, coach: Coach) -> None:
        """删除教练"""
        await db.delete(coach)
    
    @staticmethod
    async def get_list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
        organization_id: int = 1,
    ) -> tuple[list[Coach], int]:
        """获取教练列表"""
        from sqlalchemy import func
        
        query = select(Coach).where(Coach.organization_id == organization_id)
        
        if is_active is not None:
            query = query.where(Coach.is_active == is_active)
        
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        
        return result.scalars().all(), total
    
    @staticmethod
    async def add_hours(db: AsyncSession, coach: Coach, hours: float) -> Coach:
        """增加课时"""
        coach.total_hours += hours
        await db.flush()
        return coach
    
    @staticmethod
    async def add_student(db: AsyncSession, coach: Coach) -> Coach:
        """增加服务学员数"""
        coach.total_students += 1
        await db.flush()
        return coach