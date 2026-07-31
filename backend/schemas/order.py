from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    member_id: int
    amount: float = Field(gt=0)
    discount: float = 0.0
    actual_amount: float = Field(gt=0)
    product_type: Optional[str] = None
    product_id: Optional[int] = None
    subject: Optional[str] = None
    notes: Optional[str] = None


class OrderUpdate(BaseModel):
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    order_no: str
    member_id: int
    organization_id: int
    amount: float
    discount: float
    actual_amount: float
    payment_method: Optional[str] = None
    payment_status: str
    transaction_id: Optional[str] = None
    product_type: Optional[str] = None
    product_id: Optional[int] = None
    subject: Optional[str] = None
    operator_id: Optional[int] = None
    notes: Optional[str] = None
    cancel_reason: Optional[str] = None
    refund_amount: float = 0.0
    refunded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
