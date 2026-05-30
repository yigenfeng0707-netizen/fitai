"""经营分析服务"""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.order import Order, OrderStatus
from backend.models.member import Member
from backend.models.booking import Booking, BookingStatus
from backend.models.course import CourseSchedule, Course
from backend.models.coach import Coach


class AnalyticsService:
    @staticmethod
    async def get_dashboard_data(
        db: AsyncSession,
        organization_id: int,
    ) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
        thirty_days_ago = today_start - timedelta(days=29)

        # ========== 收入统计 ==========
        today_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(Order.organization_id == organization_id, Order.payment_status == OrderStatus.PAID, Order.paid_at >= today_start)
        )
        revenue_today = float(today_revenue_raw.scalar() or 0)

        week_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(Order.organization_id == organization_id, Order.payment_status == OrderStatus.PAID, Order.paid_at >= week_start)
        )
        revenue_week = float(week_revenue_raw.scalar() or 0)

        month_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(Order.organization_id == organization_id, Order.payment_status == OrderStatus.PAID, Order.paid_at >= month_start)
        )
        revenue_month = float(month_revenue_raw.scalar() or 0)

        prev_month_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= prev_month_start,
                Order.paid_at < month_start,
            )
        )
        revenue_prev_month = float(prev_month_revenue_raw.scalar() or 0)

        # ========== 日收入趋势 (30天) ==========
        revenue_trend_rows = await db.execute(
            select(
                func.date(Order.paid_at).label("date"),
                func.coalesce(func.sum(Order.actual_amount), 0).label("revenue"),
            )
            .where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= thirty_days_ago,
                Order.paid_at < today_start + timedelta(days=1),
            )
            .group_by(func.date(Order.paid_at))
            .order_by(func.date(Order.paid_at))
        )
        revenue_by_date = {r.date: float(r.revenue) for r in revenue_trend_rows}
        revenue_trend = []
        for i in range(29, -1, -1):
            day = (today_start - timedelta(days=i)).date()
            revenue_trend.append({
                "date": day.strftime("%Y-%m-%d"),
                "revenue": revenue_by_date.get(day, 0),
            })

        # ========== 会员统计 ==========
        total_members_raw = await db.execute(
            select(func.count(Member.id)).where(Member.organization_id == organization_id)
        )
        total_members = total_members_raw.scalar() or 0

        active_members_raw = await db.execute(
            select(func.count(Member.id)).where(Member.organization_id == organization_id, Member.status == "active")
        )
        active_members = active_members_raw.scalar() or 0

        new_members_month_raw = await db.execute(
            select(func.count(Member.id)).where(Member.organization_id == organization_id, Member.created_at >= month_start)
        )
        new_members_month = new_members_month_raw.scalar() or 0

        # 日新增会员趋势
        member_trend_rows = await db.execute(
            select(
                func.date(Member.created_at).label("date"),
                func.count(Member.id).label("count"),
            )
            .where(
                Member.organization_id == organization_id,
                Member.created_at >= thirty_days_ago,
                Member.created_at < today_start + timedelta(days=1),
            )
            .group_by(func.date(Member.created_at))
            .order_by(func.date(Member.created_at))
        )
        member_by_date = {r.date: r.count for r in member_trend_rows}
        member_trend = []
        for i in range(29, -1, -1):
            day = (today_start - timedelta(days=i)).date()
            member_trend.append({
                "date": day.strftime("%Y-%m-%d"),
                "count": member_by_date.get(day, 0),
            })

        # ========== 预约/签到统计 ==========
        today_bookings_raw = await db.execute(
            select(func.count(Booking.id))
            .join(CourseSchedule)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.start_time >= today_start,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                Booking.status != BookingStatus.CANCELLED,
            )
        )
        bookings_today = today_bookings_raw.scalar() or 0

        today_checked_in_raw = await db.execute(
            select(func.count(Booking.id))
            .join(CourseSchedule)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.start_time >= today_start,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                Booking.status == BookingStatus.CHECKED_IN,
            )
        )
        checked_in_today = today_checked_in_raw.scalar() or 0

        week_bookings_raw = await db.execute(
            select(func.count(Booking.id))
            .join(CourseSchedule)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.start_time >= week_start,
                CourseSchedule.start_time < week_start + timedelta(days=7),
                Booking.status != BookingStatus.CANCELLED,
            )
        )
        bookings_week = week_bookings_raw.scalar() or 0

        # 上课率 (最近30天)
        total_classes_raw = await db.execute(
            select(func.count(CourseSchedule.id))
            .where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.start_time >= thirty_days_ago,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                CourseSchedule.status != "cancelled",
            )
        )
        total_classes = total_classes_raw.scalar() or 0

        completed_classes_raw = await db.execute(
            select(func.count(CourseSchedule.id))
            .where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.start_time >= thirty_days_ago,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                CourseSchedule.status == "completed",
            )
        )
        completed_classes = completed_classes_raw.scalar() or 0
        completion_rate = round((completed_classes / total_classes * 100), 1) if total_classes > 0 else 0

        # ========== 热门课程 Top 5 (最近30天) ==========
        top_courses_query = (
            select(
                Course.name,
                func.count(Booking.id).label("booking_count"),
            )
            .join(CourseSchedule, Booking.schedule_id == CourseSchedule.id)
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.start_time >= thirty_days_ago,
                Booking.status != BookingStatus.CANCELLED,
            )
            .group_by(Course.id, Course.name)
            .order_by(func.count(Booking.id).desc())
            .limit(5)
        )
        top_courses_result = await db.execute(top_courses_query)
        top_courses = [{"name": row[0], "booking_count": row[1]} for row in top_courses_result]

        # ========== 时段分布 ==========
        from sqlalchemy import text, inspect
        # Dialect-aware SQL: SQLite uses strftime, PostgreSQL uses to_char
        bind = db.get_bind()
        dialect_name = bind.dialect.name if bind else "sqlite"
        if dialect_name == "sqlite":
            hour_sql = "strftime('%H', cs.start_time)"
        else:
            hour_sql = "to_char(cs.start_time, 'HH24')"

        hour_rows = await db.execute(
            text(f"""
                SELECT {hour_sql} AS hour, count(b.id) AS count
                FROM bookings b
                JOIN course_schedules cs ON cs.id = b.schedule_id
                WHERE b.organization_id = :org_id
                  AND cs.start_time >= :start
                  AND cs.start_time < :end
                  AND b.status != 'CANCELLED'
                GROUP BY hour
                ORDER BY hour
            """),
            {"org_id": organization_id, "start": today_start, "end": today_start + timedelta(days=1)},
        )
        count_by_hour = {int(str(r[0])): int(r[1]) for r in hour_rows}
        hour_distribution = [
            {"hour": f"{h}:00", "count": count_by_hour.get(h, 0)}
            for h in range(6, 22)
        ]

        # ========== 教练工作量 ==========
        coach_load_query = (
            select(
                Coach.name,
                func.count(CourseSchedule.id).label("class_count"),
            )
            .join(Course, Course.coach_id == Coach.id)
            .join(CourseSchedule, CourseSchedule.course_id == Course.id)
            .where(
                Coach.organization_id == organization_id,
                CourseSchedule.start_time >= week_start,
                CourseSchedule.start_time < week_start + timedelta(days=7),
            )
            .group_by(Coach.id, Coach.name)
            .order_by(func.count(CourseSchedule.id).desc())
            .limit(5)
        )
        coach_load_result = await db.execute(coach_load_query)
        coach_load = [{"name": row[0], "class_count": row[1]} for row in coach_load_result]

        return {
            "revenue": {
                "today": revenue_today,
                "week": revenue_week,
                "month": revenue_month,
                "prev_month": revenue_prev_month,
                "month_growth": round(
                    ((revenue_month - revenue_prev_month) / revenue_prev_month * 100), 1
                ) if revenue_prev_month > 0 else 100,
                "trend": revenue_trend,
            },
            "members": {
                "total": total_members,
                "active": active_members,
                "new_month": new_members_month,
                "trend": member_trend,
            },
            "bookings": {
                "today": bookings_today,
                "checked_in_today": checked_in_today,
                "week": bookings_week,
                "completion_rate": completion_rate,
                "hour_distribution": hour_distribution,
            },
            "courses": {
                "top": top_courses,
            },
            "coaches": {
                "week_load": coach_load,
            },
        }
