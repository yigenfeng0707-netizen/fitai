"""
Member-related Agent tools.

Wraps members.py and body_test API endpoints as callable tools.
"""
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.tools.registry import AgentTool, ToolRegistry
from backend.models.member import Member
from backend.models.body_test import BodyTestRecord
from backend.models.order import Order, OrderStatus
from backend.models.booking import Booking, BookingStatus


def register_member_tools(registry: ToolRegistry) -> None:
    """Register all member-related tools."""

    async def _get_member_profile(db: AsyncSession, member_id: int,
                                   organization_id: int, **_kw) -> dict:
        result = await db.execute(
            select(Member).where(
                Member.id == member_id,
                Member.organization_id == organization_id,
            )
        )
        m = result.scalar_one_or_none()
        if not m:
            return {"error": "Member not found"}
        return {
            "id": m.id,
            "name": m.name,
            "phone": m.phone,
            "gender": m.gender,
            "card_type": m.card_type.value if m.card_type else None,
            "level": m.level,
            "total_consumption": m.total_consumption,
            "status": m.status.value if m.status else None,
            "card_remaining_count": m.card_remaining_count,
            "card_balance": m.card_balance,
            "card_end_date": m.card_end_date.isoformat() if m.card_end_date else None,
        }

    async def _get_body_tests(db: AsyncSession, member_id: int,
                              organization_id: int, limit: int = 5, **_kw) -> list[dict]:
        result = await db.execute(
            select(BodyTestRecord)
            .where(
                BodyTestRecord.member_id == member_id,
                BodyTestRecord.organization_id == organization_id,
            )
            .order_by(desc(BodyTestRecord.created_at))
            .limit(limit)
        )
        records = result.scalars().all()
        return [
            {
                "date": r.created_at.isoformat() if r.created_at else None,
                "weight": r.weight,
                "body_fat_percentage": r.body_fat_percentage,
                "muscle_mass": r.muscle_mass,
                "bmi": r.bmi,
                "score": r.score,
                "basal_metabolism": r.basal_metabolism,
                "visceral_fat": r.visceral_fat,
                "body_age": r.body_age,
            }
            for r in records
        ]

    async def _get_member_consumption(db: AsyncSession, member_id: int,
                                      organization_id: int, limit: int = 10, **_kw) -> list[dict]:
        result = await db.execute(
            select(Order)
            .where(
                Order.member_id == member_id,
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
            )
            .order_by(desc(Order.paid_at))
            .limit(limit)
        )
        orders = result.scalars().all()
        return [
            {
                "order_id": o.id,
                "amount": o.actual_amount,
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
                "description": o.description if hasattr(o, "description") else None,
            }
            for o in orders
        ]

    async def _get_member_bookings(db: AsyncSession, member_id: int,
                                   organization_id: int, limit: int = 10, **_kw) -> list[dict]:
        result = await db.execute(
            select(Booking)
            .where(
                Booking.member_id == member_id,
                Booking.organization_id == organization_id,
            )
            .order_by(desc(Booking.created_at))
            .limit(limit)
        )
        bookings = result.scalars().all()
        return [
            {
                "booking_id": b.id,
                "schedule_id": b.schedule_id,
                "status": b.status.value if b.status else None,
                "check_in_time": b.check_in_time.isoformat() if b.check_in_time else None,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bookings
        ]

    async def _get_member_attendance_rate(db: AsyncSession, member_id: int,
                                          organization_id: int, **_kw) -> dict:
        result = await db.execute(
            select(
                func.count(Booking.id).label("total"),
                func.count(Booking.id).filter(
                    Booking.status == BookingStatus.COMPLETED
                ).label("attended"),
                func.count(Booking.id).filter(
                    Booking.status == BookingStatus.CANCELLED
                ).label("cancelled"),
                func.count(Booking.id).filter(
                    Booking.status == BookingStatus.NO_SHOW
                ).label("no_show"),
            )
            .where(
                Booking.member_id == member_id,
                Booking.organization_id == organization_id,
            )
        )
        row = result.one()
        total = row.total or 0
        attended = row.attended or 0
        cancelled = row.cancelled or 0
        no_show = row.no_show or 0
        rate = (attended / total * 100) if total > 0 else 0
        return {
            "total_bookings": total,
            "attended": attended,
            "cancelled": cancelled,
            "no_show": no_show,
            "attendance_rate": round(rate, 1),
        }

    registry.register(AgentTool(
        name="get_member_profile",
        description="Get member profile including card type, level, consumption, and status.",
        parameters={
            "type": "object",
            "properties": {
                "member_id": {"type": "integer", "description": "Member ID"},
            },
            "required": ["member_id"],
        },
        handler=_get_member_profile,
        category="member",
    ))

    registry.register(AgentTool(
        name="get_body_tests",
        description="Get body test records for a member, sorted by most recent first.",
        parameters={
            "type": "object",
            "properties": {
                "member_id": {"type": "integer", "description": "Member ID"},
                "limit": {"type": "integer", "description": "Number of records (default 5)", "default": 5},
            },
            "required": ["member_id"],
        },
        handler=_get_body_tests,
        category="member",
    ))

    registry.register(AgentTool(
        name="get_member_consumption",
        description="Get recent paid orders/consumption history for a member.",
        parameters={
            "type": "object",
            "properties": {
                "member_id": {"type": "integer", "description": "Member ID"},
                "limit": {"type": "integer", "description": "Number of records (default 10)", "default": 10},
            },
            "required": ["member_id"],
        },
        handler=_get_member_consumption,
        category="member",
    ))

    registry.register(AgentTool(
        name="get_member_bookings",
        description="Get recent booking history for a member.",
        parameters={
            "type": "object",
            "properties": {
                "member_id": {"type": "integer", "description": "Member ID"},
                "limit": {"type": "integer", "description": "Number of records (default 10)", "default": 10},
            },
            "required": ["member_id"],
        },
        handler=_get_member_bookings,
        category="member",
    ))

    registry.register(AgentTool(
        name="get_member_attendance_rate",
        description="Calculate attendance rate for a member: total bookings, attended, cancelled, no-show.",
        parameters={
            "type": "object",
            "properties": {
                "member_id": {"type": "integer", "description": "Member ID"},
            },
            "required": ["member_id"],
        },
        handler=_get_member_attendance_rate,
        category="member",
    ))
