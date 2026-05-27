"""
Pydantic Schema - 会员卡交易
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from backend.models.card_transaction import TransactionType
from backend.models.member import CardType


class CardRenewRequest(BaseModel):
    card_type: CardType
    duration_days: int = Field(..., ge=1, le=3650)
    amount: float = Field(0, ge=0)
    description: Optional[str] = None


class CardRechargeRequest(BaseModel):
    amount: float = Field(..., gt=0)
    count: int = Field(0, ge=0)
    description: Optional[str] = None


class CardUpgradeRequest(BaseModel):
    new_card_type: CardType
    amount: float = Field(0, ge=0)
    description: Optional[str] = None


class CardTransactionResponse(BaseModel):
    id: int
    member_id: int
    transaction_type: TransactionType
    amount: float
    count_change: int
    balance_before: float
    balance_after: float
    count_before: int
    count_after: int
    card_type_before: Optional[str] = None
    card_type_after: Optional[str] = None
    description: Optional[str] = None
    operator_id: Optional[int] = None
    order_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExpiringCardResponse(BaseModel):
    member_id: int
    member_name: str
    member_phone: str
    card_type: Optional[CardType] = None
    card_end_date: Optional[datetime] = None
    days_remaining: int
