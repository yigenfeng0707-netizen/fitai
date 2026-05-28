"""
CRUD - 会员卡交易
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.card_transaction import CardTransaction, TransactionType
from backend.models.member import Member, CardType, MemberStatus
from backend.schemas.card_transaction import CardRenewRequest, CardRechargeRequest, CardUpgradeRequest


class CardTransactionCRUD:
    @staticmethod
    async def renew(
        db: AsyncSession,
        member: Member,
        req: CardRenewRequest,
        operator_id: Optional[int] = None,
    ) -> CardTransaction:
        old_card_type = member.card_type.value if member.card_type else None
        now = datetime.utcnow()

        if member.card_end_date and member.card_end_date > now:
            new_end = member.card_end_date + timedelta(days=req.duration_days)
        else:
            new_end = now + timedelta(days=req.duration_days)

        member.card_type = req.card_type
        member.card_end_date = new_end
        if not member.card_start_date:
            member.card_start_date = now

        txn = CardTransaction(
            member_id=member.id,
            organization_id=member.organization_id,
            transaction_type=TransactionType.RENEW,
            amount=req.amount,
            card_type_before=old_card_type,
            card_type_after=req.card_type.value,
            balance_before=member.card_balance,
            balance_after=member.card_balance,
            count_before=member.card_remaining_count,
            count_after=member.card_remaining_count,
            description=req.description or f"续费 {req.card_type.value} {req.duration_days}天",
            operator_id=operator_id,
        )

        db.add(txn)
        await db.flush()
        return txn

    @staticmethod
    async def recharge(
        db: AsyncSession,
        member: Member,
        req: CardRechargeRequest,
        operator_id: Optional[int] = None,
    ) -> CardTransaction:
        balance_before = member.card_balance
        count_before = member.card_remaining_count

        if req.count > 0:
            member.card_remaining_count += req.count
            member.card_type = CardType.SINGLE
        if req.amount > 0:
            member.card_balance += req.amount
            if req.count == 0:
                member.card_type = CardType.STORED

        txn = CardTransaction(
            member_id=member.id,
            organization_id=member.organization_id,
            transaction_type=TransactionType.RECHARGE,
            amount=req.amount,
            count_change=req.count,
            balance_before=balance_before,
            balance_after=member.card_balance,
            count_before=count_before,
            count_after=member.card_remaining_count,
            card_type_before=member.card_type.value if member.card_type else None,
            card_type_after=member.card_type.value if member.card_type else None,
            description=req.description or f"充值 余额+{req.amount} 次数+{req.count}",
            operator_id=operator_id,
        )

        db.add(txn)
        await db.flush()
        return txn

    @staticmethod
    async def upgrade(
        db: AsyncSession,
        member: Member,
        req: CardUpgradeRequest,
        operator_id: Optional[int] = None,
    ) -> CardTransaction:
        old_card_type = member.card_type.value if member.card_type else None
        now = datetime.utcnow()

        member.card_type = req.new_card_type

        duration_map = {
            CardType.MONTHLY: 30,
            CardType.QUARTERLY: 90,
            CardType.YEARLY: 365,
        }

        if req.new_card_type in duration_map:
            if member.card_end_date and member.card_end_date > now:
                member.card_end_date = now + timedelta(days=duration_map[req.new_card_type])
            else:
                member.card_end_date = now + timedelta(days=duration_map[req.new_card_type])
            member.card_start_date = now
        elif req.new_card_type == CardType.SINGLE:
            member.card_end_date = None
        elif req.new_card_type == CardType.STORED:
            member.card_end_date = None

        txn = CardTransaction(
            member_id=member.id,
            organization_id=member.organization_id,
            transaction_type=TransactionType.UPGRADE,
            amount=req.amount,
            card_type_before=old_card_type,
            card_type_after=req.new_card_type.value,
            balance_before=member.card_balance,
            balance_after=member.card_balance,
            count_before=member.card_remaining_count,
            count_after=member.card_remaining_count,
            description=req.description or f"升级卡 {old_card_type} → {req.new_card_type.value}",
            operator_id=operator_id,
        )

        db.add(txn)
        await db.flush()
        return txn

    @staticmethod
    async def get_member_transactions(
        db: AsyncSession,
        member_id: int,
        skip: int = 0,
        limit: int = 20,
        transaction_type: Optional[TransactionType] = None,
    ) -> tuple[list[CardTransaction], int]:
        query = select(CardTransaction).where(CardTransaction.member_id == member_id)
        if transaction_type:
            query = query.where(CardTransaction.transaction_type == transaction_type)
        query = query.order_by(CardTransaction.created_at.desc())

        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total

    @staticmethod
    async def get_expiring_cards(
        db: AsyncSession,
        organization_id: int,
        days: int = 7,
    ) -> list[dict]:
        now = datetime.utcnow()
        deadline = now + timedelta(days=days)

        query = (
            select(Member)
            .where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
                Member.card_end_date.isnot(None),
                Member.card_end_date >= now,
                Member.card_end_date <= deadline,
            )
            .order_by(Member.card_end_date.asc())
        )
        result = await db.execute(query)
        members = result.scalars().all()

        return [
            {
                "member_id": m.id,
                "member_name": m.name,
                "member_phone": m.phone,
                "card_type": m.card_type.value if m.card_type else None,
                "card_end_date": m.card_end_date.isoformat() if m.card_end_date else None,
                "days_remaining": (m.card_end_date - now).days if m.card_end_date else 0,
            }
            for m in members
        ]

    @staticmethod
    async def get_expired_cards(
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Member], int]:
        now = datetime.utcnow()
        query = (
            select(Member)
            .where(
                Member.organization_id == organization_id,
                Member.card_end_date.isnot(None),
                Member.card_end_date < now,
            )
            .order_by(Member.card_end_date.desc())
        )
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total
