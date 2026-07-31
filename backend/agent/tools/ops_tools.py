"""
Operations and analytics related Agent tools.

Wraps dashboard.py, analytics.py, and orders.py API endpoints.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.tools.registry import AgentTool, ToolRegistry
from backend.models.member import Member, MemberStatus
from backend.models.order import Order, OrderStatus
from backend.models.booking import Booking, BookingStatus
from backend.models.course import Course, CourseSchedule


def register_ops_tools(registry: ToolRegistry) -> None:
    """Register all operations and analytics tools."""

    async def _get_dashboard_insights(db: AsyncSession, organization_id: int, **_kw) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        today_rev = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0)).where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= today_start,
            )
        )
        revenue_today = float(today_rev.scalar() or 0)

        month_rev = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0)).where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= month_start,
            )
        )
        revenue_month = float(month_rev.scalar() or 0)

        active_count = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
            )
        )
        active_members = active_count.scalar() or 0

        new_count = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.created_at >= month_start,
            )
        )
        new_members_month = new_count.scalar() or 0

        bookings_today = await db.execute(
            select(func.count(Booking.id)).where(
                Booking.organization_id == organization_id,
                Booking.created_at >= today_start,
            )
        )
        bookings_count = bookings_today.scalar() or 0

        top = await db.execute(
            select(Course.name, func.count(Booking.id).label("cnt"))
            .join(CourseSchedule, CourseSchedule.course_id == Course.id)
            .join(Booking, Booking.schedule_id == CourseSchedule.id)
            .where(
                Course.organization_id == organization_id,
                Booking.organization_id == organization_id,
            )
            .group_by(Course.name)
            .order_by(desc("cnt"))
            .limit(5)
        )
        top_courses = [{"name": r[0], "booking_count": r[1]} for r in top.all()]

        insights = []
        if revenue_month > 0:
            insights.append(f"Month revenue: {revenue_month:.0f}")
        if new_members_month > 0:
            insights.append(f"New members this month: {new_members_month}")
        if active_members > 0 and new_members_month / max(active_members, 1) > 0.2:
            insights.append(f"New member ratio high: {new_members_month/active_members*100:.0f}%")

        return {
            "revenue_today": revenue_today,
            "revenue_month": revenue_month,
            "active_members": active_members,
            "new_members_month": new_members_month,
            "bookings_today": bookings_count,
            "top_courses": top_courses,
            "insights": insights,
        }

    async def _get_revenue_stats(db: AsyncSession, organization_id: int,
                                 date_from: str = "", date_to: str = "", **_kw) -> dict:
        stmt = select(
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.actual_amount), 0).label("total_revenue"),
            func.coalesce(func.avg(Order.actual_amount), 0).label("avg_order_value"),
        ).where(
            Order.organization_id == organization_id,
            Order.payment_status == OrderStatus.PAID,
        )
        if date_from:
            try:
                dt = datetime.fromisoformat(date_from)
                stmt = stmt.where(Order.paid_at >= dt)
            except ValueError:
                pass
        if date_to:
            try:
                dt = datetime.fromisoformat(date_to)
                stmt = stmt.where(Order.paid_at <= dt)
            except ValueError:
                pass
        result = await db.execute(stmt)
        row = result.one()
        return {
            "order_count": row.order_count or 0,
            "total_revenue": float(row.total_revenue or 0),
            "avg_order_value": float(row.avg_order_value or 0),
        }

    async def _get_member_retention(db: AsyncSession, organization_id: int, **_kw) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        month_ago = now - timedelta(days=30)
        three_month_ago = now - timedelta(days=90)

        total_members = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
            )
        )
        total = total_members.scalar() or 0

        active_30 = await db.execute(
            select(func.count(func.distinct(Booking.member_id))).where(
                Booking.organization_id == organization_id,
                Booking.created_at >= month_ago,
            )
        )
        active_30_count = active_30.scalar() or 0

        active_90 = await db.execute(
            select(func.count(func.distinct(Booking.member_id))).where(
                Booking.organization_id == organization_id,
                Booking.created_at >= three_month_ago,
            )
        )
        active_90_count = active_90.scalar() or 0

        retention_30 = (active_30_count / total * 100) if total > 0 else 0
        retention_90 = (active_90_count / total * 100) if total > 0 else 0
        return {
            "total_active_members": total,
            "active_in_30_days": active_30_count,
            "active_in_90_days": active_90_count,
            "retention_30d": round(retention_30, 1),
            "retention_90d": round(retention_90, 1),
        }

    async def _get_dormant_members(db: AsyncSession, organization_id: int,
                                   days: int = 30, limit: int = 20, **_kw) -> list[dict]:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        active_member_ids = await db.execute(
            select(func.distinct(Booking.member_id)).where(
                Booking.organization_id == organization_id,
                Booking.created_at >= cutoff,
            )
        )
        active_ids = {r[0] for r in active_member_ids.all()}

        stmt = select(Member).where(
            Member.organization_id == organization_id,
            Member.status == MemberStatus.ACTIVE,
        )
        if active_ids:
            stmt = stmt.where(~Member.id.in_(active_ids))
        stmt = stmt.order_by(Member.total_consumption.desc()).limit(limit)
        result = await db.execute(stmt)
        members = result.scalars().all()
        return [
            {
                "id": m.id,
                "name": m.name,
                "phone": m.phone,
                "last_consumption": m.total_consumption,
                "level": m.level,
                "card_type": m.card_type.value if m.card_type else None,
            }
            for m in members
        ]

    registry.register(AgentTool(
        name="get_dashboard_insights",
        description="Get business dashboard: today/month revenue, active members, new members, top courses, and auto-generated insights.",
        parameters={"type": "object", "properties": {}},
        handler=_get_dashboard_insights,
        category="operations",
    ))

    registry.register(AgentTool(
        name="get_revenue_stats",
        description="Get revenue statistics: order count, total revenue, average order value. Supports date range filter.",
        parameters={
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
            },
        },
        handler=_get_revenue_stats,
        category="operations",
    ))

    registry.register(AgentTool(
        name="get_member_retention",
        description="Get member retention metrics: how many members active in last 30/90 days vs total.",
        parameters={"type": "object", "properties": {}},
        handler=_get_member_retention,
        category="operations",
    ))

    registry.register(AgentTool(
        name="get_dormant_members",
        description="Find members who haven't booked in N days (default 30). Useful for churn prevention.",
        parameters={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Days of inactivity (default 30)", "default": 30},
                "limit": {"type": "integer", "description": "Max results (default 20)", "default": 20},
            },
        },
        handler=_get_dormant_members,
        category="operations",
    ))
