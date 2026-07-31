"""
Course and booking related Agent tools.

Wraps courses.py and bookings.py API endpoints as callable tools.
"""
from datetime import datetime, date
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.tools.registry import AgentTool, ToolRegistry
from backend.models.course import Course, CourseSchedule, CourseType
from backend.models.booking import Booking, BookingStatus
from backend.models.coach import Coach


def register_course_tools(registry: ToolRegistry) -> None:
    """Register all course and booking related tools."""

    async def _search_courses(db: AsyncSession, organization_id: int,
                              course_type: str = "", coach_id: int = 0, **_kw) -> list[dict]:
        stmt = select(Course).where(
            Course.organization_id == organization_id,
            Course.is_active.is_(True),
        )
        if course_type:
            try:
                ct = CourseType(course_type)
                stmt = stmt.where(Course.course_type == ct)
            except ValueError:
                pass
        if coach_id:
            stmt = stmt.where(Course.coach_id == coach_id)
        result = await db.execute(stmt)
        courses = result.scalars().all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "course_type": c.course_type.value if c.course_type else None,
                "duration_minutes": c.duration_minutes,
                "price": c.price,
                "room": c.room,
                "max_attendees": c.max_attendees,
                "coach_id": c.coach_id,
            }
            for c in courses
        ]

    async def _get_course_schedule(db: AsyncSession, organization_id: int,
                                   date_from: str = "", date_to: str = "",
                                   course_id: int = 0, **_kw) -> list[dict]:
        stmt = select(CourseSchedule).where(
            CourseSchedule.organization_id == organization_id,
        )
        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                stmt = stmt.where(CourseSchedule.start_time >= dt_from)
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                stmt = stmt.where(CourseSchedule.start_time <= dt_to)
            except ValueError:
                pass
        if course_id:
            stmt = stmt.where(CourseSchedule.course_id == course_id)
        stmt = stmt.order_by(CourseSchedule.start_time)
        result = await db.execute(stmt.limit(50))
        schedules = result.scalars().all()
        return [
            {
                "id": s.id,
                "course_id": s.course_id,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "status": s.status,
                "enrolled_count": s.enrolled_count,
            }
            for s in schedules
        ]

    async def _book_course(db: AsyncSession, member_id: int, schedule_id: int,
                           organization_id: int, **_kw) -> dict:
        existing = await db.execute(
            select(Booking).where(
                Booking.member_id == member_id,
                Booking.schedule_id == schedule_id,
                Booking.organization_id == organization_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            )
        )
        if existing.scalar_one_or_none():
            return {"error": "Member already has an active booking for this schedule"}

        schedule_result = await db.execute(
            select(CourseSchedule).where(
                CourseSchedule.id == schedule_id,
                CourseSchedule.organization_id == organization_id,
            )
        )
        schedule = schedule_result.scalar_one_or_none()
        if not schedule:
            return {"error": "Schedule not found"}
        if schedule.status == "cancelled":
            return {"error": "This schedule has been cancelled"}

        booking = Booking(
            member_id=member_id,
            schedule_id=schedule_id,
            organization_id=organization_id,
            status=BookingStatus.PENDING,
        )
        db.add(booking)
        schedule.enrolled_count = (schedule.enrolled_count or 0) + 1
        await db.flush()
        return {
            "booking_id": booking.id,
            "status": booking.status.value,
            "schedule_id": schedule_id,
            "member_id": member_id,
            "message": "Booking created successfully",
        }

    async def _cancel_booking(db: AsyncSession, booking_id: int,
                              organization_id: int, **_kw) -> dict:
        result = await db.execute(
            select(Booking).where(
                Booking.id == booking_id,
                Booking.organization_id == organization_id,
            )
        )
        booking = result.scalar_one_or_none()
        if not booking:
            return {"error": "Booking not found"}
        if booking.status in (BookingStatus.CANCELLED, BookingStatus.COMPLETED):
            return {"error": f"Cannot cancel booking with status: {booking.status.value}"}
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        await db.flush()
        return {"booking_id": booking_id, "status": "cancelled", "message": "Booking cancelled"}

    async def _check_schedule_conflict(db: AsyncSession, organization_id: int,
                                       coach_id: int = 0, date_from: str = "",
                                       date_to: str = "", **_kw) -> list[dict]:
        stmt = select(CourseSchedule, Course).join(
            Course, CourseSchedule.course_id == Course.id
        ).where(
            CourseSchedule.organization_id == organization_id,
            CourseSchedule.status != "cancelled",
        )
        if coach_id:
            stmt = stmt.where(Course.coach_id == coach_id)
        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                stmt = stmt.where(CourseSchedule.start_time >= dt_from)
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                stmt = stmt.where(CourseSchedule.start_time <= dt_to)
            except ValueError:
                pass
        stmt = stmt.order_by(CourseSchedule.start_time)
        result = await db.execute(stmt)
        rows = result.all()

        conflicts = []
        for i in range(len(rows) - 1):
            curr, curr_course = rows[i]
            nxt, nxt_course = rows[i + 1]
            if curr.end_time > nxt.start_time:
                overlap = (curr.end_time - nxt.start_time).total_seconds() / 60
                conflicts.append({
                    "schedule_1_id": curr.id,
                    "schedule_1_course": curr_course.name,
                    "schedule_1_time": f"{curr.start_time.strftime('%Y-%m-%d %H:%M')}-{curr.end_time.strftime('%H:%M')}",
                    "schedule_2_id": nxt.id,
                    "schedule_2_course": nxt_course.name,
                    "schedule_2_time": f"{nxt.start_time.strftime('%Y-%m-%d %H:%M')}-{nxt.end_time.strftime('%H:%M')}",
                    "overlap_minutes": round(overlap),
                })
        return conflicts

    registry.register(AgentTool(
        name="search_courses",
        description="Search available courses, optionally filtered by type (group/private/semi_private) or coach.",
        parameters={
            "type": "object",
            "properties": {
                "course_type": {"type": "string", "description": "Course type: group, private, semi_private"},
                "coach_id": {"type": "integer", "description": "Coach ID to filter by"},
            },
        },
        handler=_search_courses,
        category="course",
    ))

    registry.register(AgentTool(
        name="get_course_schedule",
        description="Get course schedule list, optionally filtered by date range or course ID.",
        parameters={
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                "course_id": {"type": "integer", "description": "Course ID to filter"},
            },
        },
        handler=_get_course_schedule,
        category="course",
    ))

    registry.register(AgentTool(
        name="book_course",
        description="Book a course schedule for a member. Creates a pending booking.",
        parameters={
            "type": "object",
            "properties": {
                "member_id": {"type": "integer", "description": "Member ID"},
                "schedule_id": {"type": "integer", "description": "Course schedule ID"},
            },
            "required": ["member_id", "schedule_id"],
        },
        handler=_book_course,
        category="course",
    ))

    registry.register(AgentTool(
        name="cancel_booking",
        description="Cancel an existing booking by booking ID.",
        parameters={
            "type": "object",
            "properties": {
                "booking_id": {"type": "integer", "description": "Booking ID to cancel"},
            },
            "required": ["booking_id"],
        },
        handler=_cancel_booking,
        category="course",
    ))

    registry.register(AgentTool(
        name="check_schedule_conflict",
        description="Detect scheduling conflicts (overlapping time slots) for a coach or the entire store.",
        parameters={
            "type": "object",
            "properties": {
                "coach_id": {"type": "integer", "description": "Coach ID to check conflicts for"},
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
            },
        },
        handler=_check_schedule_conflict,
        category="course",
    ))
