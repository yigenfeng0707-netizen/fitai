from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.order import Order, OrderStatus
from backend.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from backend.schemas.common import BaseResponse, ListResponse
from backend.services.order import OrderService
from backend.services.payment import payment_service

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    obj_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = await OrderService.create(
        db, obj_in,
        organization_id=current_user.organization_id,
        operator_id=current_user.id,
    )
    return order


@router.get("/", response_model=ListResponse[OrderResponse])
async def get_orders(
    member_id: Optional[int] = None,
    payment_status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    status_enum = OrderStatus(payment_status) if payment_status else None
    orders, total = await OrderService.get_list(
        db, skip=skip, limit=limit,
        member_id=member_id,
        payment_status=status_enum,
        organization_id=current_user.organization_id,
    )
    return ListResponse(
        data=orders,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = await OrderService.get(db, order_id)
    if not order or order.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    return order


@router.post("/{order_id}/pay", response_model=BaseResponse)
async def pay_order(
    order_id: int,
    payment_method: str = Query(..., description="wechat or alipay"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = await OrderService.get(db, order_id)
    if not order or order.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    if order.payment_status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单状态不允许支付",
        )

    gateway = payment_service.get_gateway(payment_method)
    result = await gateway.create_payment(
        order_no=order.order_no,
        subject=order.subject or "商品购买",
        amount=order.actual_amount,
    )

    if result.success and result.trade_no:
        await OrderService.pay(db, order, payment_method, result.trade_no)
        from backend.services.audit import AuditService
        await AuditService.log(db, action="pay", resource="order", resource_id=order.id, detail=f"订单 {order.order_no} 支付 {order.actual_amount}元", user_id=current_user.id, organization_id=current_user.organization_id)

    return BaseResponse(
        success=result.success,
        message="支付成功" if result.success else "支付失败",
        data={"redirect_url": result.redirect_url, "trade_no": result.trade_no},
    )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = await OrderService.get(db, order_id)
    if not order or order.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    if order.payment_status == OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已支付订单请使用退款",
        )
    order = await OrderService.cancel(db, order, reason)
    return order


@router.post("/{order_id}/refund", response_model=OrderResponse)
async def refund_order(
    order_id: int,
    amount: float = Query(..., gt=0),
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = await OrderService.get(db, order_id)
    if not order or order.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    if order.payment_status != OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已支付订单可以退款",
        )
    order = await OrderService.refund(db, order, amount, reason)
    return order


@router.post("/notify/{payment_method}", include_in_schema=False)
async def payment_notify(
    payment_method: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.json()
    gateway = payment_service.get_gateway(payment_method)
    data = await gateway.verify_notification(body)
    order_no = data.get("order_no", "")
    transaction_id = data.get("trade_no", "")

    order = await OrderService.get_by_no(db, order_no)
    if order and order.payment_status == OrderStatus.PENDING:
        await OrderService.pay(db, order, payment_method, transaction_id)

    return {"code": "SUCCESS", "message": "OK"}
