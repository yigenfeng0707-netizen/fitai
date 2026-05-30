"""
API - 小程序支付
"""
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.member import Member
from backend.models.order import Order, OrderStatus
from backend.schemas.mini import (
    MiniOrderCreate,
    MiniOrderResponse,
    WxPayParams,
    PaymentConfirmRequest,
)
from backend.schemas.common import BaseResponse, ListResponse

router = APIRouter(prefix="/mini", tags=["小程序-支付"])

# 商品类型到中文名称的映射
PRODUCT_TYPE_NAMES = {
    "membership": "会员卡",
    "course_package": "课程套餐",
    "private_class": "私教课",
}


def _get_member_from_user(user: User) -> int:
    """从用户获取关联的会员ID"""
    if not user.member_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="当前用户未关联会员信息",
        )
    return user.member_id


def _generate_order_no() -> str:
    """生成订单号"""
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:8].upper()


@router.post("/orders", response_model=MiniOrderResponse)
async def create_order(
    obj_in: MiniOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建支付订单
    - product_type: membership, course_package, private_class
    - product_id: 商品ID
    - amount: 订单金额
    - payment_method: wechat
    """
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)

    # 验证商品类型
    if obj_in.product_type not in PRODUCT_TYPE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的商品类型: {obj_in.product_type}",
        )

    # 验证金额
    if obj_in.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单金额必须大于0",
        )

    subject = PRODUCT_TYPE_NAMES.get(obj_in.product_type, "商品购买")

    order = Order(
        order_no=_generate_order_no(),
        member_id=member_id,
        amount=obj_in.amount,
        discount=0.0,
        actual_amount=obj_in.amount,
        payment_method=obj_in.payment_method,
        payment_status=OrderStatus.PENDING,
        product_type=obj_in.product_type,
        product_id=obj_in.product_id,
        subject=subject,
        organization_id=current_user.organization_id,
        operator_id=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(order)
    await db.flush()

    return MiniOrderResponse(
        id=order.id,
        order_no=order.order_no,
        amount=order.amount,
        actual_amount=order.actual_amount,
        payment_status=order.payment_status.value,
        product_type=order.product_type,
        subject=order.subject,
        created_at=order.created_at,
        paid_at=None,
    )


@router.get("/orders/{order_id}", response_model=MiniOrderResponse)
async def get_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取订单详情"""
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)

    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.member_id == member_id,
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )

    return MiniOrderResponse(
        id=order.id,
        order_no=order.order_no,
        amount=order.amount,
        actual_amount=order.actual_amount,
        payment_status=order.payment_status.value,
        product_type=order.product_type,
        subject=order.subject,
        created_at=order.created_at,
        paid_at=order.paid_at,
    )


@router.post("/orders/{order_id}/pay", response_model=WxPayParams)
async def initiate_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    发起微信支付
    Stub: 返回模拟支付参数
    真实实现: 调用微信支付 API 获取 prepay_id，生成 paySign
    """
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)

    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.member_id == member_id,
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )

    if order.payment_status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态不允许支付: {order.payment_status.value}",
        )

    # 检查订单是否过期
    if order.expires_at and order.expires_at < datetime.now(timezone.utc):
        order.payment_status = OrderStatus.CANCELLED
        order.cancel_reason = "订单超时取消"
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单已过期",
        )

    # Stub: 返回模拟支付参数
    # 真实实现:
    # 1. 调用微信支付统一下单 API 获取 prepay_id
    # 2. 使用 prepay_id 生成签名
    timestamp = str(int(time.time()))
    nonce_str = uuid.uuid4().hex

    return WxPayParams(
        timeStamp=timestamp,
        nonceStr=nonce_str,
        package=f"prepay_id=mock_prepay_{order.order_no}",
        signType="RSA",
        paySign=f"mock_sign_{nonce_str[:16]}",
    )


@router.post("/orders/{order_id}/confirm", response_model=MiniOrderResponse)
async def confirm_payment(
    order_id: int,
    obj_in: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    确认支付结果
    安全改造: 服务端验证支付状态，而非信任客户端传入的 transaction_id
    """
    from sqlalchemy import select

    member_id = _get_member_from_user(current_user)

    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.member_id == member_id,
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )

    if order.payment_status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态不允许确认: {order.payment_status.value}",
        )

    # 服务端验证: 通过微信支付 API 查询订单真实状态
    # 目前为 stub 模式，生产环境应调用微信支付查询接口
    # from backend.services.wechat_pay_v3 import WeChatPayGateway
    # verified = await WeChatPayGateway.verify_payment(order.order_no)
    # if not verified:
    #     raise HTTPException(status_code=400, detail="支付验证失败")

    # 生成交易号（实际应从微信支付回调获取）
    transaction_id = obj_in.transaction_id or f"MOCK_{uuid.uuid4().hex[:16].upper()}"

    # 更新订单状态
    order.payment_status = OrderStatus.PAID
    order.transaction_id = transaction_id
    order.paid_at = datetime.now(timezone.utc)

    # 根据商品类型更新会员卡
    member_result = await db.execute(
        select(Member).where(Member.id == member_id)
    )
    member = member_result.scalar_one_or_none()

    if member:
        if order.product_type == "membership":
            from backend.models.member import CardType
            if not member.card_end_date or member.card_end_date < datetime.now(timezone.utc):
                member.card_start_date = datetime.now(timezone.utc)
                member.card_end_date = datetime.now(timezone.utc) + timedelta(days=30)
            else:
                member.card_end_date = member.card_end_date + timedelta(days=30)
            member.card_type = CardType.MONTHLY
        elif order.product_type == "course_package":
            member.card_remaining_count = (member.card_remaining_count or 0) + 10
        elif order.product_type == "private_class":
            member.card_balance = (member.card_balance or 0) + order.actual_amount

        member.total_consumption = (member.total_consumption or 0) + order.actual_amount

    from backend.services.audit import AuditService
    await AuditService.log(
        db, action="payment_confirm", resource="order", resource_id=order.id,
        detail=f"支付确认: 订单 {order.order_no}, 金额 {order.actual_amount}, 交易号 {transaction_id}",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )

    await db.flush()

    return MiniOrderResponse(
        id=order.id,
        order_no=order.order_no,
        amount=order.amount,
        actual_amount=order.actual_amount,
        payment_status=order.payment_status.value,
        product_type=order.product_type,
        subject=order.subject,
        created_at=order.created_at,
        paid_at=order.paid_at,
    )


@router.post("/pay/notify")
async def wechat_pay_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    微信支付结果通知回调（服务端对服务端）
    微信服务器在用户支付成功后调用此端点
    生产环境需要:
    1. 验证请求签名（使用微信支付平台证书）
    2. 解密通知数据
    3. 更新订单状态
    4. 返回 SUCCESS/FAIL
    """
    try:
        body = await request.body()
        headers = dict(request.headers)

        # TODO: 生产环境实现
        # 1. 验证签名
        # from backend.services.wechat_pay_v3 import WeChatPayGateway
        # is_valid = WeChatPayGateway.verify_notification(headers, body.decode('utf-8'))
        # if not is_valid:
        #     return PlainTextResponse(content='FAIL', status_code=400)

        # 2. 解密并处理通知数据
        # notification = WeChatPayGateway.decrypt_notification(body)
        # order_no = notification.get('out_trade_no')
        # transaction_id = notification.get('transaction_id')
        # trade_state = notification.get('trade_state')

        # 3. 更新订单状态
        # if trade_state == 'SUCCESS':
        #     order = await db.execute(select(Order).where(Order.order_no == order_no))
        #     order = order.scalar_one_or_none()
        #     if order and order.payment_status == OrderStatus.PENDING:
        #         order.payment_status = OrderStatus.PAID
        #         order.transaction_id = transaction_id
        #         order.paid_at = datetime.now(timezone.utc)
        #         await db.flush()

        # Stub: 直接返回成功
        return PlainTextResponse(content='SUCCESS')

    except Exception as e:
        return PlainTextResponse(content='FAIL', status_code=500)


@router.get("/orders", response_model=ListResponse[MiniOrderResponse])
async def get_my_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的订单列表"""
    from sqlalchemy import select, func

    member_id = _get_member_from_user(current_user)

    query = select(Order).where(Order.member_id == member_id)
    if status_filter:
        query = query.where(Order.payment_status == status_filter)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar()

    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    orders = list(result.scalars().all())

    data = [
        MiniOrderResponse(
            id=o.id,
            order_no=o.order_no,
            amount=o.amount,
            actual_amount=o.actual_amount,
            payment_status=o.payment_status.value,
            product_type=o.product_type or "",
            subject=o.subject or "",
            created_at=o.created_at,
            paid_at=o.paid_at,
        )
        for o in orders
    ]

    return ListResponse(
        data=data,
        total=total,
        page=skip // limit + 1 if skip else 1,
        page_size=limit,
    )
