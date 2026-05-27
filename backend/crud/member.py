"""
CRUD - 会员
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.member import Member, CardType, MemberStatus
from backend.schemas.member import MemberCreate, MemberUpdate


class MemberCRUD:
    """会员 CRUD"""
    
    @staticmethod
    async def get(db: AsyncSession, member_id: int) -> Optional[Member]:
        """获取会员"""
        result = await db.execute(
            select(Member).where(Member.id == member_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[Member]:
        """通过手机号获取会员"""
        result = await db.execute(
            select(Member).where(Member.phone == phone)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, obj_in: MemberCreate, organization_id: int = 1) -> Member:
        """创建会员"""
        card_remaining_count = 0
        card_balance = 0.0
        card_start_date = None
        card_end_date = None
        
        # 初始化卡信息
        if obj_in.initial_card_type == CardType.SINGLE and obj_in.initial_card_count:
            card_remaining_count = obj_in.initial_card_count
            card_start_date = datetime.utcnow()
        elif obj_in.initial_card_type == CardType.STORED and obj_in.initial_card_balance:
            card_balance = obj_in.initial_card_balance
            card_start_date = datetime.utcnow()
        elif obj_in.initial_card_type in [CardType.MONTHLY, CardType.QUARTERLY, CardType.YEARLY]:
            card_start_date = datetime.utcnow()
            # 计算到期日
            if obj_in.initial_card_type == CardType.MONTHLY:
                card_end_date = datetime.utcnow().replace(day=28) + timedelta(days=4)
            elif obj_in.initial_card_type == CardType.QUARTERLY:
                card_end_date = datetime.utcnow().replace(day=28) + timedelta(days=4) * 3
            else:
                card_end_date = datetime.utcnow().replace(day=28) + timedelta(days=4) * 12
        
        member = Member(
            name=obj_in.name,
            phone=obj_in.phone,
            email=obj_in.email,
            gender=obj_in.gender,
            birthday=obj_in.birthday,
            card_type=obj_in.initial_card_type,
            card_start_date=card_start_date,
            card_end_date=card_end_date,
            card_remaining_count=card_remaining_count,
            card_balance=card_balance,
            coach_id=obj_in.coach_id,
            organization_id=organization_id,
        )
        
        db.add(member)
        await db.flush()
        return member
    
    @staticmethod
    async def update(db: AsyncSession, member: Member, obj_in: MemberUpdate) -> Member:
        """更新会员"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(member, field, value)
        
        await db.flush()
        return member
    
    @staticmethod
    async def delete(db: AsyncSession, member: Member) -> None:
        """删除会员"""
        await db.delete(member)
    
    @staticmethod
    async def get_list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[MemberStatus] = None,
        search: Optional[str] = None,
        organization_id: int = 1,
    ) -> tuple[list[Member], int]:
        """获取会员列表"""
        query = select(Member).where(Member.organization_id == organization_id)
        
        if status:
            query = query.where(Member.status == status)
        
        if search:
            query = query.where(
                (Member.name.ilike(f"%{search}%")) |
                (Member.phone.ilike(f"%{search}%"))
            )
        
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        
        return result.scalars().all(), total
    
    @staticmethod
    async def add_consumption(db: AsyncSession, member: Member, amount: float) -> Member:
        """增加消费记录"""
        member.total_consumption += amount
        if member.level == 1 and member.total_consumption >= 1000:
            member.level = 2
        elif member.level == 2 and member.total_consumption >= 5000:
            member.level = 3
        elif member.level == 3 and member.total_consumption >= 10000:
            member.level = 4
        elif member.level == 4 and member.total_consumption >= 20000:
            member.level = 5
        
        await db.flush()
        return member
    
    @staticmethod
    async def deduct_session(db: AsyncSession, member: Member) -> Member:
        """扣除次卡次数"""
        if member.card_type == CardType.SINGLE and member.card_remaining_count > 0:
            member.card_remaining_count -= 1
            await db.flush()
        return member