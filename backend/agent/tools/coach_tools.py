"""
Coach-related Agent tools.

Wraps coaches.py API endpoints as callable tools.
"""
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.tools.registry import AgentTool, ToolRegistry
from backend.models.coach import Coach
from backend.models.course import Course, CourseSchedule


def register_coach_tools(registry: ToolRegistry) -> None:
    """Register all coach-related tools."""

    async def _get_coach_profile(db: AsyncSession, coach_id: int,
                                 organization_id: int, **_kw) -> dict:
        result = await db.execute(
            select(Coach).where(
                Coach.id == coach_id,
                Coach.organization_id == organization_id,
            )
        )
        c = result.scalar_one_or_none()
        if not c:
            return {"error": "Coach not found"}
        return {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "specialization": c.specialization,
            "introduction": c.introduction,
            "certificates": c.certificates,
            "total_hours": c.total_hours,
            "total_students": c.total_students,
            "avg_rating": c.avg_rating,
            "is_active": c.is_active,
            "work_schedule": c.work_schedule,
        }

    async def _list_coaches(db: AsyncSession, organization_id: int, **_kw) -> list[dict]:
        result = await db.execute(
            select(Coach).where(
                Coach.organization_id == organization_id,
                Coach.is_active.is_(True),
            )
        )
        coaches = result.scalars().all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "specialization": c.specialization,
                "total_hours": c.total_hours,
                "avg_rating": c.avg_rating,
            }
            for c in coaches
        ]

    async def _get_coach_schedule(db: AsyncSession, coach_id: int,
                                  organization_id: int, **_kw) -> list[dict]:
        result = await db.execute(
            select(CourseSchedule, Course)
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(
                Course.coach_id == coach_id,
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.status != "cancelled",
            )
            .order_by(CourseSchedule.start_time)
        )
        rows = result.all()
        return [
            {
                "schedule_id": s.id,
                "course_name": c.name,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "status": s.status,
                "enrolled_count": s.enrolled_count,
            }
            for s, c in rows
        ]

    async def _get_coach_stats(db: AsyncSession, coach_id: int,
                               organization_id: int, **_kw) -> dict:
        result = await db.execute(
            select(
                func.count(CourseSchedule.id).label("total_sessions"),
                func.count(CourseSchedule.id).filter(
                    CourseSchedule.status == "completed"
                ).label("completed_sessions"),
                func.count(CourseSchedule.id).filter(
                    CourseSchedule.status == "scheduled"
                ).label("upcoming_sessions"),
            )
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(
                Course.coach_id == coach_id,
                CourseSchedule.organization_id == organization_id,
            )
        )
        row = result.one()
        coach_result = await db.execute(
            select(Coach).where(
                Coach.id == coach_id,
                Coach.organization_id == organization_id,
            )
        )
        coach = coach_result.scalar_one_or_none()
        return {
            "coach_id": coach_id,
            "coach_name": coach.name if coach else None,
            "total_sessions": row.total_sessions or 0,
            "completed_sessions": row.completed_sessions or 0,
            "upcoming_sessions": row.upcoming_sessions or 0,
            "total_hours": coach.total_hours if coach else 0,
            "avg_rating": coach.avg_rating if coach else 0,
        }

    registry.register(AgentTool(
        name="get_coach_profile",
        description="Get coach profile including specialization, certificates, rating, and work schedule.",
        parameters={
            "type": "object",
            "properties": {
                "coach_id": {"type": "integer", "description": "Coach ID"},
            },
            "required": ["coach_id"],
        },
        handler=_get_coach_profile,
        category="coach",
    ))

    registry.register(AgentTool(
        name="list_coaches",
        description="List all active coaches in the current organization.",
        parameters={"type": "object", "properties": {}},
        handler=_list_coaches,
        category="coach",
    ))

    registry.register(AgentTool(
        name="get_coach_schedule",
        description="Get upcoming and past course schedules for a specific coach.",
        parameters={
            "type": "object",
            "properties": {
                "coach_id": {"type": "integer", "description": "Coach ID"},
            },
            "required": ["coach_id"],
        },
        handler=_get_coach_schedule,
        category="coach",
    ))

    registry.register(AgentTool(
        name="get_coach_stats",
        description="Get teaching statistics for a coach: total sessions, completed, upcoming, hours, rating.",
        parameters={
            "type": "object",
            "properties": {
                "coach_id": {"type": "integer", "description": "Coach ID"},
            },
            "required": ["coach_id"],
        },
        handler=_get_coach_stats,
        category="coach",
    ))
