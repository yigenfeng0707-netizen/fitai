"""
API - 会员卡管理
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.member import Member
from backend.models.card_transaction import TransactionType
from backend.schemas.card_transaction import (
    CardRenewRequest,
    CardRechargeRequest,
    CardUpgradeRequest,
    CardTransactionResponse,
    ExpiringCardResponse,
)
from backend.schemas.member import MemberResponse
from backend.schemas.common import ListResponse

router = APIRouter()


async def _get_member_or_404(db: AsyncSession, member_id: int, org_id: int) -> Member:
    from backend.crud.member import MemberCRUD
    member = await MemberCRUD.get(db, member_id)
    if not member or member.organization_id != org_id:
        raise HTTPException(status_code=404, detail="会员不存在")
    return member


@router.post("/{member_id}/renew", response_model=CardTransactionResponse)
async def renew_card(
    member_id: int,
    req: CardRenewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = await _get_member_or_404(db, member_id, current_user.organization_id)
    from backend.crud.card_transaction import CardTransactionCRUD
    txn = await CardTransactionCRUD.renew(db, member, req, operator_id=current_user.id)
    from backend.services.audit import AuditService
    await AuditService.log(db, action="card_renew", resource="member", resource_id=member_id, detail=f"续费 {req.card_type.value} {req.duration_days}天 ¥{req.amount}", user_id=current_user.id, organization_id=current_user.organization_id)
    return txn


@router.post("/{member_id}/recharge", response_model=CardTransactionResponse)
async def recharge_card(
    member_id: int,
    req: CardRechargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = await _get_member_or_404(db, member_id, current_user.organization_id)
    from backend.crud.card_transaction import CardTransactionCRUD
    txn = await CardTransactionCRUD.recharge(db, member, req, operator_id=current_user.id)
    return txn


@router.post("/{member_id}/upgrade", response_model=CardTransactionResponse)
async def upgrade_card(
    member_id: int,
    req: CardUpgradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = await _get_member_or_404(db, member_id, current_user.organization_id)
    from backend.crud.card_transaction import CardTransactionCRUD
    txn = await CardTransactionCRUD.upgrade(db, member, req, operator_id=current_user.id)
    return txn


@router.get("/{member_id}/transactions", response_model=ListResponse[CardTransactionResponse])
async def get_card_transactions(
    member_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    transaction_type: Optional[TransactionType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_member_or_404(db, member_id, current_user.organization_id)
    from backend.crud.card_transaction import CardTransactionCRUD
    txns, total = await CardTransactionCRUD.get_member_transactions(
        db, member_id, current_user.organization_id, skip=skip, limit=limit, transaction_type=transaction_type,
    )
    return ListResponse(data=txns, total=total, page=skip // limit + 1, page_size=limit)


@router.get("/expiring", response_model=list[ExpiringCardResponse])
async def get_expiring_cards(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.card_transaction import CardTransactionCRUD
    return await CardTransactionCRUD.get_expiring_cards(db, current_user.organization_id, days=days)


@router.get("/expired", response_model=ListResponse[MemberResponse])
async def get_expired_cards(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.crud.card_transaction import CardTransactionCRUD
    members, total = await CardTransactionCRUD.get_expired_cards(
        db, current_user.organization_id, skip=skip, limit=limit,
    )
    return ListResponse(data=members, total=total, page=skip // limit + 1, page_size=limit)
