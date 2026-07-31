"""
Member long-term memory store.

Combines structured data (body tests, bookings, consumption) with
optional vector retrieval for similar member pattern matching.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.member import Member
from backend.models.body_test import BodyTestRecord
from backend.models.booking import Booking, BookingStatus
from backend.models.order import Order, OrderStatus

logger = logging.getLogger(__name__)


class MemberMemoryStore:
    """Stores and retrieves member-level context for Agent interactions."""

    async def retrieve(self, member_id: int, organization_id: int,
                       db: AsyncSession) -> str:
        """
        Retrieve relevant member memory as a text context block.

        Combines:
        - Latest 3 body test records with trend
        - Last 10 bookings with attendance rate
        - Consumption summary
        - Member level and card info
        """
        parts = []

        # Member basic info
        member_result = await db.execute(
            select(Member).where(
                Member.id == member_id,
                Member.organization_id == organization_id,
            )
        )
        member = member_result.scalar_one_or_none()
        if not member:
            return ""
        parts.append(
            f"Member: {member.name} (ID:{member_id}), "
            f"Level:{member.level}, Card:{member.card_type.value if member.card_type else 'N/A'}, "
            f"Total spent:{member.total_consumption or 0}, "
            f"Status:{member.status.value if member.status else 'unknown'}"
        )

        # Latest body tests
        test_result = await db.execute(
            select(BodyTestRecord)
            .where(
                BodyTestRecord.member_id == member_id,
                BodyTestRecord.organization_id == organization_id,
            )
            .order_by(desc(BodyTestRecord.created_at))
            .limit(3)
        )
        tests = test_result.scalars().all()
        if tests:
            latest = tests[0]
            test_str = (
                f"Latest body test ({latest.created_at.date() if latest.created_at else 'N/A'}): "
                f"weight={latest.weight}kg, body_fat={latest.body_fat_percentage}%, "
                f"BMI={latest.bmi}, muscle={latest.muscle_mass}kg, score={latest.score}"
            )
            if len(tests) > 1:
                prev = tests[1]
                if latest.weight and prev.weight:
                    diff = latest.weight - prev.weight
                    test_str += f" | Weight change: {diff:+.1f}kg"
                if latest.body_fat_percentage and prev.body_fat_percentage:
                    bf_diff = latest.body_fat_percentage - prev.body_fat_percentage
                    test_str += f" | Body fat change: {bf_diff:+.1f}%"
            parts.append(test_str)

        # Booking history summary
        booking_result = await db.execute(
            select(Booking).where(
                Booking.member_id == member_id,
                Booking.organization_id == organization_id,
            )
            .order_by(desc(Booking.created_at))
            .limit(10)
        )
        bookings = booking_result.scalars().all()
        if bookings:
            attended = sum(1 for b in bookings if b.status == BookingStatus.COMPLETED)
            cancelled = sum(1 for b in bookings if b.status == BookingStatus.CANCELLED)
            no_show = sum(1 for b in bookings if b.status == BookingStatus.NO_SHOW)
            rate = attended / len(bookings) * 100 if bookings else 0
            parts.append(
                f"Recent 10 bookings: attended={attended}, cancelled={cancelled}, "
                f"no_show={no_show}, attendance_rate={rate:.0f}%"
            )

        # Consumption summary
        order_result = await db.execute(
            select(
                func_count(Order.id),
                func_coalesce_sum(Order.actual_amount),
            ).where(
                Order.member_id == member_id,
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
            )
        )
        row = order_result.one()
        if row[0] and row[0] > 0:
            parts.append(f"Total paid orders: {row[0]}, total amount: {row[1]:.0f}")

        return "\n".join(parts) if parts else ""

    async def store(self, member_id: int, organization_id: int, db: AsyncSession,
                    user_query: str, agent_answer: str, tool_calls: list) -> None:
        """Store interaction to database for long-term memory and audit."""
        try:
            from backend.models.agent_log import AgentInteractionLog
            log_entry = AgentInteractionLog(
                organization_id=organization_id,
                member_id=member_id,
                user_input=user_query,
                agent_answer=agent_answer,
                tool_calls=tool_calls,
                iterations=len(tool_calls),
            )
            db.add(log_entry)
            await db.commit()
            logger.info(
                "Agent interaction stored: member=%d org=%d query='%s' tools=%d",
                member_id, organization_id, user_query[:50], len(tool_calls),
            )
        except Exception:
            logger.warning("Failed to store agent interaction", exc_info=True)
            await db.rollback()


# Helper functions to avoid importing func at module level in complex queries
from sqlalchemy import func as _func

def func_count(column):
    return _func.count(column)

def func_coalesce_sum(column):
    return _func.coalesce(_func.sum(column), 0)
