from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.services.order import OrderService
from backend.services.receipt import ReceiptService

router = APIRouter()


@router.get("/orders/{order_id}/receipt")
async def download_receipt(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = await OrderService.get(db, order_id)
    if not order or order.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="订单不存在")

    member_name = ""
    if order.member_id:
        from backend.models.member import Member
        from sqlalchemy import select
        result = await db.execute(select(Member).where(Member.id == order.member_id))
        member = result.scalar_one_or_none()
        if member:
            member_name = member.name

    from sqlalchemy import select
    from backend.models.organization import Organization
    org_result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = org_result.scalar_one_or_none()
    org_name = org.name if org else "FitAI"

    paid_at_str = None
    if order.paid_at:
        paid_at_str = order.paid_at.strftime("%Y-%m-%d %H:%M") if hasattr(order.paid_at, 'strftime') else str(order.paid_at)

    pdf_bytes = ReceiptService.generate_order_receipt(
        order_no=order.order_no,
        member_name=member_name,
        subject=order.subject or "商品购买",
        amount=order.amount,
        discount=order.discount or 0,
        actual_amount=order.actual_amount,
        payment_method=order.payment_method or "",
        payment_status=order.payment_status if isinstance(order.payment_status, str) else order.payment_status.value if hasattr(order.payment_status, 'value') else str(order.payment_status),
        paid_at=paid_at_str,
        org_name=org_name,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="receipt_{order.order_no}.pdf"'},
    )
