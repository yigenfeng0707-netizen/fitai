"""
数据可视化仪表盘服务
聚合多数据源，为前端图表提供统一 API
"""
from datetime import datetime, timedelta

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.order import Order, OrderStatus
from backend.models.member import Member, MemberStatus
from backend.models.booking import Booking, BookingStatus
from backend.models.course import CourseSchedule, Course
from backend.models.coach import Coach
from backend.models.store import Store


# 周期映射：period -> timedelta
_PERIOD_DELTA: dict[str, timedelta] = {
    "today": timedelta(days=1),
    "week": timedelta(weeks=1),
    "month": timedelta(days=30),
    "quarter": timedelta(days=90),
    "year": timedelta(days=365),
}


def _change_direction(current: float, previous: float) -> tuple[float, str]:
    """计算变化百分比和方向"""
    if previous == 0:
        pct = 100.0 if current > 0 else 0.0
    else:
        pct = round((current - previous) / previous * 100, 1)
    direction = "up" if pct > 0 else ("down" if pct < 0 else "flat")
    return pct, direction


def _get_period_range(period: str, now: datetime):
    """根据 period 返回 (start, end, prev_start) 三个时间点"""
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "today":
        start = today_start
        end = today_start + timedelta(days=1)
        prev_start = today_start - timedelta(days=1)
    elif period == "week":
        start = today_start - timedelta(days=today_start.weekday())
        end = start + timedelta(days=7)
        prev_start = start - timedelta(days=7)
    elif period == "month":
        start = today_start.replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        prev_start = (start - timedelta(days=1)).replace(day=1)
    elif period == "quarter":
        month_in_quarter = (now.month - 1) % 3
        start = today_start.replace(day=1) - timedelta(days=month_in_quarter * 30)
        end = start + timedelta(days=90)
        prev_start = start - timedelta(days=90)
    else:  # year
        start = today_start.replace(month=1, day=1)
        end = today_start.replace(year=now.year + 1, month=1, day=1)
        prev_start = today_start.replace(year=now.year - 1, month=1, day=1)

    return start, end, prev_start


class DashboardService:
    """数据可视化仪表盘服务"""

    @staticmethod
    async def get_executive_dashboard(
        db: AsyncSession,
        organization_id: int,
        period: str = "month",
    ) -> dict:
        """
        高管仪表盘 - 一屏概览所有关键指标
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = today_start - timedelta(days=29)
        month_start = today_start.replace(day=1)
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

        period_start, period_end, prev_period_start = _get_period_range(period, now)

        # ========== KPI 指标 ==========

        # 总营收 (当前周期)
        revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= period_start,
                Order.paid_at < period_end,
            )
        )
        total_revenue = float(revenue_raw.scalar() or 0)

        # 上一周期营收
        prev_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= prev_period_start,
                Order.paid_at < period_start,
            )
        )
        prev_revenue = float(prev_revenue_raw.scalar() or 0)
        revenue_growth, revenue_dir = _change_direction(total_revenue, prev_revenue)

        # 总会员数
        total_members_raw = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
            )
        )
        total_members = total_members_raw.scalar() or 0

        # 上一周期新增会员
        prev_new_members_raw = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.created_at >= prev_period_start,
                Member.created_at < period_start,
            )
        )
        prev_new_members = prev_new_members_raw.scalar() or 0

        # 当前周期新增会员
        new_members_raw = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.created_at >= period_start,
                Member.created_at < period_end,
            )
        )
        new_members = new_members_raw.scalar() or 0
        member_growth, member_dir = _change_direction(float(new_members), float(prev_new_members))

        # 今日预约数
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
        today_bookings = today_bookings_raw.scalar() or 0

        # 签到率 (最近30天)
        total_bookings_30_raw = await db.execute(
            select(func.count(Booking.id))
            .join(CourseSchedule)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.start_time >= thirty_days_ago,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                Booking.status != BookingStatus.CANCELLED,
            )
        )
        total_bookings_30 = total_bookings_30_raw.scalar() or 0

        checked_in_30_raw = await db.execute(
            select(func.count(Booking.id))
            .join(CourseSchedule)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.start_time >= thirty_days_ago,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                Booking.status == BookingStatus.CHECKED_IN,
            )
        )
        checked_in_30 = checked_in_30_raw.scalar() or 0
        checkin_rate = round((checked_in_30 / total_bookings_30 * 100), 1) if total_bookings_30 > 0 else 0.0

        # 活跃门店数
        active_stores_raw = await db.execute(
            select(func.count(Store.id)).where(
                Store.organization_id == organization_id,
                Store.is_active == True,  # noqa: E712
            )
        )
        active_stores = active_stores_raw.scalar() or 0

        # NPS 评分 (用平均教练评分近似)
        nps_raw = await db.execute(
            select(func.coalesce(func.avg(Coach.avg_rating), 0)).where(
                Coach.organization_id == organization_id,
            )
        )
        nps_score = round(float(nps_raw.scalar() or 0), 1)

        kpi = {
            "total_revenue": {
                "label": "总营收",
                "value": total_revenue,
                "unit": "元",
                "change": revenue_growth,
                "change_direction": revenue_dir,
                "icon": "revenue",
            },
            "revenue_growth": {
                "label": "营收增长",
                "value": revenue_growth,
                "unit": "%",
                "change": None,
                "change_direction": revenue_dir,
                "icon": "trending",
            },
            "total_members": {
                "label": "总会员数",
                "value": total_members,
                "unit": "人",
                "change": member_growth,
                "change_direction": member_dir,
                "icon": "users",
            },
            "member_growth": {
                "label": "会员增长",
                "value": new_members,
                "unit": "人",
                "change": member_growth,
                "change_direction": member_dir,
                "icon": "user-plus",
            },
            "today_bookings": {
                "label": "今日预约",
                "value": today_bookings,
                "unit": "次",
                "change": None,
                "change_direction": None,
                "icon": "calendar",
            },
            "checkin_rate": {
                "label": "签到率",
                "value": checkin_rate,
                "unit": "%",
                "change": None,
                "change_direction": None,
                "icon": "check-circle",
            },
            "active_stores": {
                "label": "活跃门店",
                "value": active_stores,
                "unit": "家",
                "change": None,
                "change_direction": None,
                "icon": "store",
            },
            "nps_score": {
                "label": "满意度评分",
                "value": nps_score,
                "unit": "分",
                "change": None,
                "change_direction": None,
                "icon": "star",
            },
        }

        # ========== 30天营收趋势 ==========
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
        revenue_chart_data = []
        for i in range(29, -1, -1):
            day = (today_start - timedelta(days=i)).date()
            revenue_chart_data.append({
                "label": day.strftime("%m-%d"),
                "value": revenue_by_date.get(day, 0),
            })

        revenue_chart = {
            "chart_type": "line",
            "title": "营收趋势 (近30天)",
            "data": revenue_chart_data,
            "colors": ["#4F46E5"],
        }

        # ========== 会员增长趋势 ==========
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
        member_chart_data = []
        for i in range(29, -1, -1):
            day = (today_start - timedelta(days=i)).date()
            member_chart_data.append({
                "label": day.strftime("%m-%d"),
                "value": float(member_by_date.get(day, 0)),
            })

        member_chart = {
            "chart_type": "bar",
            "title": "会员增长趋势 (近30天)",
            "data": member_chart_data,
            "colors": ["#10B981"],
        }

        # ========== 预约趋势 ==========
        booking_trend_rows = await db.execute(
            select(
                func.date(CourseSchedule.start_time).label("date"),
                func.count(Booking.id).label("count"),
            )
            .join(Booking, Booking.schedule_id == CourseSchedule.id)
            .where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.start_time >= thirty_days_ago,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                Booking.status != BookingStatus.CANCELLED,
            )
            .group_by(func.date(CourseSchedule.start_time))
            .order_by(func.date(CourseSchedule.start_time))
        )
        booking_by_date = {r.date: r.count for r in booking_trend_rows}
        booking_chart_data = []
        for i in range(29, -1, -1):
            day = (today_start - timedelta(days=i)).date()
            booking_chart_data.append({
                "label": day.strftime("%m-%d"),
                "value": float(booking_by_date.get(day, 0)),
            })

        booking_chart = {
            "chart_type": "line",
            "title": "预约趋势 (近30天)",
            "data": booking_chart_data,
            "colors": ["#F59E0B"],
        }

        # ========== 门店排名 ==========
        store_revenue_rows = await db.execute(
            select(
                Store.id,
                Store.name,
                func.coalesce(func.sum(Order.actual_amount), 0).label("revenue"),
            )
            .outerjoin(Order, (Order.store_id == Store.id) & (Order.payment_status == OrderStatus.PAID) & (Order.paid_at >= period_start) & (Order.paid_at < period_end))
            .where(Store.organization_id == organization_id)
            .group_by(Store.id, Store.name)
            .order_by(func.coalesce(func.sum(Order.actual_amount), 0).desc())
            .limit(10)
        )
        store_ranking = []
        for rank, row in enumerate(store_revenue_rows, 1):
            store_ranking.append({
                "rank": rank,
                "store_id": row.id,
                "store_name": row.name,
                "value": float(row.revenue),
                "change": 0.0,  # 简化处理
            })

        # ========== 热门课程 ==========
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
        top_courses = [
            {"name": row[0], "booking_count": row[1]}
            for row in top_courses_result
        ]

        # ========== 预警信息 ==========
        alerts = await DashboardService.get_dashboard_alerts(db, organization_id)

        return {
            "kpi": kpi,
            "revenue_chart": revenue_chart,
            "member_chart": member_chart,
            "booking_chart": booking_chart,
            "store_ranking": store_ranking,
            "top_courses": top_courses,
            "alerts": alerts,
        }

    @staticmethod
    async def get_store_dashboard(
        db: AsyncSession,
        store_id: int,
        organization_id: int,
        period: str = "month",
    ) -> dict:
        """
        门店仪表盘 - 单门店详情
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = today_start - timedelta(days=29)

        period_start, period_end, prev_period_start = _get_period_range(period, now)

        # ========== KPI ==========

        # 门店营收
        revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(
                Order.organization_id == organization_id,
                Order.store_id == store_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= period_start,
                Order.paid_at < period_end,
            )
        )
        total_revenue = float(revenue_raw.scalar() or 0)

        prev_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(
                Order.organization_id == organization_id,
                Order.store_id == store_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= prev_period_start,
                Order.paid_at < period_start,
            )
        )
        prev_revenue = float(prev_revenue_raw.scalar() or 0)
        revenue_growth, revenue_dir = _change_direction(total_revenue, prev_revenue)

        # 门店会员数
        store_members_raw = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.store_id == store_id,
            )
        )
        store_members = store_members_raw.scalar() or 0

        # 今日预约
        today_bookings_raw = await db.execute(
            select(func.count(Booking.id))
            .join(CourseSchedule)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.store_id == store_id,
                CourseSchedule.start_time >= today_start,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                Booking.status != BookingStatus.CANCELLED,
            )
        )
        today_bookings = today_bookings_raw.scalar() or 0

        # 今日签到
        today_checkins_raw = await db.execute(
            select(func.count(Booking.id))
            .join(CourseSchedule)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.store_id == store_id,
                CourseSchedule.start_time >= today_start,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                Booking.status == BookingStatus.CHECKED_IN,
            )
        )
        today_checkins = today_checkins_raw.scalar() or 0

        # 课程完成率 (30天)
        total_classes_raw = await db.execute(
            select(func.count(CourseSchedule.id)).where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.store_id == store_id,
                CourseSchedule.start_time >= thirty_days_ago,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                CourseSchedule.status != "cancelled",
            )
        )
        total_classes = total_classes_raw.scalar() or 0

        completed_classes_raw = await db.execute(
            select(func.count(CourseSchedule.id)).where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.store_id == store_id,
                CourseSchedule.start_time >= thirty_days_ago,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                CourseSchedule.status == "completed",
            )
        )
        completed_classes = completed_classes_raw.scalar() or 0
        completion_rate = round((completed_classes / total_classes * 100), 1) if total_classes > 0 else 0.0

        kpi = {
            "total_revenue": {
                "label": "门店营收",
                "value": total_revenue,
                "unit": "元",
                "change": revenue_growth,
                "change_direction": revenue_dir,
                "icon": "revenue",
            },
            "store_members": {
                "label": "门店会员",
                "value": store_members,
                "unit": "人",
                "change": None,
                "change_direction": None,
                "icon": "users",
            },
            "today_bookings": {
                "label": "今日预约",
                "value": today_bookings,
                "unit": "次",
                "change": None,
                "change_direction": None,
                "icon": "calendar",
            },
            "today_checkins": {
                "label": "今日签到",
                "value": today_checkins,
                "unit": "人",
                "change": None,
                "change_direction": None,
                "icon": "check-circle",
            },
            "completion_rate": {
                "label": "课程完成率",
                "value": completion_rate,
                "unit": "%",
                "change": None,
                "change_direction": None,
                "icon": "target",
            },
        }

        # ========== 今日课程表 ==========
        today_schedule_rows = await db.execute(
            select(
                CourseSchedule.id,
                Course.name,
                CourseSchedule.start_time,
                CourseSchedule.end_time,
                CourseSchedule.enrolled_count,
                Course.max_attendees,
                Coach.name.label("coach_name"),
            )
            .join(Course, CourseSchedule.course_id == Course.id)
            .outerjoin(Coach, Course.coach_id == Coach.id)
            .where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.store_id == store_id,
                CourseSchedule.start_time >= today_start,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                CourseSchedule.status != "cancelled",
            )
            .order_by(CourseSchedule.start_time)
        )
        today_schedule = []
        for row in today_schedule_rows:
            today_schedule.append({
                "schedule_id": row.id,
                "course_name": row.name,
                "start_time": row.start_time.isoformat() if row.start_time else None,
                "end_time": row.end_time.isoformat() if row.end_time else None,
                "enrolled_count": row.enrolled_count,
                "max_attendees": row.max_attendees,
                "coach_name": row.coach_name,
            })

        # ========== 营收趋势 ==========
        revenue_trend_rows = await db.execute(
            select(
                func.date(Order.paid_at).label("date"),
                func.coalesce(func.sum(Order.actual_amount), 0).label("revenue"),
            )
            .where(
                Order.organization_id == organization_id,
                Order.store_id == store_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= thirty_days_ago,
                Order.paid_at < today_start + timedelta(days=1),
            )
            .group_by(func.date(Order.paid_at))
            .order_by(func.date(Order.paid_at))
        )
        revenue_by_date = {r.date: float(r.revenue) for r in revenue_trend_rows}
        revenue_chart_data = []
        for i in range(29, -1, -1):
            day = (today_start - timedelta(days=i)).date()
            revenue_chart_data.append({
                "label": day.strftime("%m-%d"),
                "value": revenue_by_date.get(day, 0),
            })

        revenue_chart = {
            "chart_type": "line",
            "title": "门店营收趋势 (近30天)",
            "data": revenue_chart_data,
            "colors": ["#4F46E5"],
        }

        # ========== 会员趋势 ==========
        member_trend_rows = await db.execute(
            select(
                func.date(Member.created_at).label("date"),
                func.count(Member.id).label("count"),
            )
            .where(
                Member.organization_id == organization_id,
                Member.store_id == store_id,
                Member.created_at >= thirty_days_ago,
                Member.created_at < today_start + timedelta(days=1),
            )
            .group_by(func.date(Member.created_at))
            .order_by(func.date(Member.created_at))
        )
        member_by_date = {r.date: r.count for r in member_trend_rows}
        member_chart_data = []
        for i in range(29, -1, -1):
            day = (today_start - timedelta(days=i)).date()
            member_chart_data.append({
                "label": day.strftime("%m-%d"),
                "value": float(member_by_date.get(day, 0)),
            })

        member_chart = {
            "chart_type": "bar",
            "title": "门店会员增长 (近30天)",
            "data": member_chart_data,
            "colors": ["#10B981"],
        }

        # ========== 教练表现 ==========
        coach_perf_query = (
            select(
                Coach.id,
                Coach.name,
                func.count(CourseSchedule.id).label("class_count"),
                func.coalesce(func.sum(Booking.id).filter(Booking.status == BookingStatus.CHECKED_IN), 0).label("checkin_count"),
            )
            .join(Course, Course.coach_id == Coach.id)
            .join(CourseSchedule, CourseSchedule.course_id == Course.id)
            .outerjoin(Booking, Booking.schedule_id == CourseSchedule.id)
            .where(
                Coach.organization_id == organization_id,
                CourseSchedule.store_id == store_id,
                CourseSchedule.start_time >= thirty_days_ago,
                CourseSchedule.start_time < today_start + timedelta(days=1),
            )
            .group_by(Coach.id, Coach.name)
            .order_by(func.count(CourseSchedule.id).desc())
            .limit(5)
        )
        coach_perf_result = await db.execute(coach_perf_query)
        coach_performance = []
        for row in coach_perf_result:
            coach_performance.append({
                "coach_id": row.id,
                "coach_name": row.name,
                "class_count": row.class_count,
                "checkin_count": row.checkin_count,
            })

        # ========== 24小时预约分布 ==========
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
                  AND cs.store_id = :store_id
                  AND cs.start_time >= :start
                  AND cs.start_time < :end
                  AND b.status != 'CANCELLED'
                GROUP BY hour
                ORDER BY hour
            """),
            {
                "org_id": organization_id,
                "store_id": store_id,
                "start": thirty_days_ago,
                "end": today_start + timedelta(days=1),
            },
        )
        count_by_hour = {int(str(r[0])): int(r[1]) for r in hour_rows}
        hourly_data = []
        for h in range(6, 22):
            hourly_data.append({
                "label": f"{h}:00",
                "value": float(count_by_hour.get(h, 0)),
            })

        hourly_distribution = {
            "chart_type": "bar",
            "title": "预约时段分布 (近30天)",
            "data": hourly_data,
            "colors": ["#8B5CF6"],
        }

        return {
            "kpi": kpi,
            "today_schedule": today_schedule,
            "revenue_chart": revenue_chart,
            "member_chart": member_chart,
            "coach_performance": coach_performance,
            "hourly_distribution": hourly_distribution,
        }

    @staticmethod
    async def get_realtime_data(
        db: AsyncSession,
        organization_id: int,
    ) -> dict:
        """
        实时数据 - 当前营业状态
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # ========== 今日统计 ==========
        today_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= today_start,
            )
        )
        today_revenue = float(today_revenue_raw.scalar() or 0)

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
        today_bookings = today_bookings_raw.scalar() or 0

        today_checkins_raw = await db.execute(
            select(func.count(Booking.id))
            .join(CourseSchedule)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.start_time >= today_start,
                CourseSchedule.start_time < today_start + timedelta(days=1),
                Booking.status == BookingStatus.CHECKED_IN,
            )
        )
        today_checkins = today_checkins_raw.scalar() or 0

        today_stats = {
            "revenue": today_revenue,
            "bookings": today_bookings,
            "checkins": today_checkins,
        }

        # ========== 正在进行的课程 ==========
        ongoing_rows = await db.execute(
            select(
                CourseSchedule.id,
                Course.name,
                CourseSchedule.start_time,
                CourseSchedule.end_time,
                CourseSchedule.enrolled_count,
                Coach.name.label("coach_name"),
                Store.name.label("store_name"),
            )
            .join(Course, CourseSchedule.course_id == Course.id)
            .outerjoin(Coach, Course.coach_id == Coach.id)
            .outerjoin(Store, CourseSchedule.store_id == Store.id)
            .where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.start_time <= now,
                CourseSchedule.end_time > now,
                CourseSchedule.status != "cancelled",
            )
            .order_by(CourseSchedule.start_time)
        )
        ongoing_classes = []
        for row in ongoing_rows:
            ongoing_classes.append({
                "schedule_id": row.id,
                "course_name": row.name,
                "start_time": row.start_time.isoformat() if row.start_time else None,
                "end_time": row.end_time.isoformat() if row.end_time else None,
                "enrolled_count": row.enrolled_count,
                "coach_name": row.coach_name,
                "store_name": row.store_name,
            })

        # ========== 即将开始的课程 (未来2小时) ==========
        upcoming_rows = await db.execute(
            select(
                CourseSchedule.id,
                Course.name,
                CourseSchedule.start_time,
                CourseSchedule.end_time,
                CourseSchedule.enrolled_count,
                Coach.name.label("coach_name"),
                Store.name.label("store_name"),
            )
            .join(Course, CourseSchedule.course_id == Course.id)
            .outerjoin(Coach, Course.coach_id == Coach.id)
            .outerjoin(Store, CourseSchedule.store_id == Store.id)
            .where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.start_time > now,
                CourseSchedule.start_time <= now + timedelta(hours=2),
                CourseSchedule.status != "cancelled",
            )
            .order_by(CourseSchedule.start_time)
        )
        upcoming_classes = []
        for row in upcoming_rows:
            upcoming_classes.append({
                "schedule_id": row.id,
                "course_name": row.name,
                "start_time": row.start_time.isoformat() if row.start_time else None,
                "end_time": row.end_time.isoformat() if row.end_time else None,
                "enrolled_count": row.enrolled_count,
                "coach_name": row.coach_name,
                "store_name": row.store_name,
            })

        # ========== 在线员工数 ==========
        staff_online_raw = await db.execute(
            select(func.count(Coach.id)).where(
                Coach.organization_id == organization_id,
                Coach.is_active == True,  # noqa: E712
            )
        )
        staff_online = staff_online_raw.scalar() or 0

        # ========== 预警 ==========
        alerts = await DashboardService.get_dashboard_alerts(db, organization_id)

        return {
            "today_stats": today_stats,
            "ongoing_classes": ongoing_classes,
            "upcoming_classes": upcoming_classes,
            "staff_online": staff_online,
            "alerts": alerts,
        }

    @staticmethod
    async def get_year_over_year_comparison(
        db: AsyncSession,
        organization_id: int,
        metric: str = "revenue",
    ) -> dict:
        """
        同比分析 - 今年 vs 去年
        """
        now = datetime.utcnow()
        current_year = now.year
        prev_year = current_year - 1

        months = [f"{m}月" for m in range(1, 13)]

        current_year_data = []
        previous_year_data = []

        for month in range(1, 13):
            month_start = datetime(current_year, month, 1)
            if month == 12:
                month_end = datetime(current_year + 1, 1, 1)
            else:
                month_end = datetime(current_year, month + 1, 1)

            prev_month_start = datetime(prev_year, month, 1)
            if month == 12:
                prev_month_end = datetime(prev_year + 1, 1, 1)
            else:
                prev_month_end = datetime(prev_year, month + 1, 1)

            if metric == "revenue":
                curr_raw = await db.execute(
                    select(func.coalesce(func.sum(Order.actual_amount), 0))
                    .where(
                        Order.organization_id == organization_id,
                        Order.payment_status == OrderStatus.PAID,
                        Order.paid_at >= month_start,
                        Order.paid_at < month_end,
                    )
                )
                prev_raw = await db.execute(
                    select(func.coalesce(func.sum(Order.actual_amount), 0))
                    .where(
                        Order.organization_id == organization_id,
                        Order.payment_status == OrderStatus.PAID,
                        Order.paid_at >= prev_month_start,
                        Order.paid_at < prev_month_end,
                    )
                )
            elif metric == "members":
                curr_raw = await db.execute(
                    select(func.count(Member.id)).where(
                        Member.organization_id == organization_id,
                        Member.created_at >= month_start,
                        Member.created_at < month_end,
                    )
                )
                prev_raw = await db.execute(
                    select(func.count(Member.id)).where(
                        Member.organization_id == organization_id,
                        Member.created_at >= prev_month_start,
                        Member.created_at < prev_month_end,
                    )
                )
            else:  # bookings
                curr_raw = await db.execute(
                    select(func.count(Booking.id))
                    .join(CourseSchedule)
                    .where(
                        Booking.organization_id == organization_id,
                        CourseSchedule.start_time >= month_start,
                        CourseSchedule.start_time < month_end,
                        Booking.status != BookingStatus.CANCELLED,
                    )
                )
                prev_raw = await db.execute(
                    select(func.count(Booking.id))
                    .join(CourseSchedule)
                    .where(
                        Booking.organization_id == organization_id,
                        CourseSchedule.start_time >= prev_month_start,
                        CourseSchedule.start_time < prev_month_end,
                        Booking.status != BookingStatus.CANCELLED,
                    )
                )

            current_year_data.append({
                "label": f"{month}月",
                "value": float(curr_raw.scalar() or 0),
            })
            previous_year_data.append({
                "label": f"{month}月",
                "value": float(prev_raw.scalar() or 0),
            })

        return {
            "current_year": current_year_data,
            "previous_year": previous_year_data,
            "months": months,
        }

    @staticmethod
    async def get_dashboard_alerts(
        db: AsyncSession,
        organization_id: int,
    ) -> list[dict]:
        """
        仪表盘预警
        - 即将到期的会员卡
        - 高流失风险会员
        - 异常营收波动
        - 课程满课率过低
        """
        now = datetime.utcnow()
        alerts = []

        # ========== 即将到期的会员卡 (30天内) ==========
        expiring_soon_raw = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.card_end_date.isnot(None),
                Member.card_end_date > now,
                Member.card_end_date <= now + timedelta(days=30),
                Member.status == MemberStatus.ACTIVE,
            )
        )
        expiring_count = expiring_soon_raw.scalar() or 0
        if expiring_count > 0:
            alerts.append({
                "type": "warning",
                "title": "会员卡即将到期",
                "message": f"有 {expiring_count} 位会员的会员卡将在30天内到期",
                "count": expiring_count,
                "action_url": "/members?filter=expiring",
            })

        # ========== 已过期的会员卡 ==========
        expired_raw = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.card_end_date.isnot(None),
                Member.card_end_date <= now,
                Member.status == MemberStatus.ACTIVE,
            )
        )
        expired_count = expired_raw.scalar() or 0
        if expired_count > 0:
            alerts.append({
                "type": "danger",
                "title": "会员卡已过期",
                "message": f"有 {expired_count} 位会员的会员卡已过期但状态仍为活跃",
                "count": expired_count,
                "action_url": "/members?filter=expired",
            })

        # ========== 高流失风险会员 (30天无预约) ==========
        at_risk_raw = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
                Member.created_at < now - timedelta(days=30),
            )
        )
        total_active_long = at_risk_raw.scalar() or 0

        if total_active_long > 0:
            # 查找30天内有预约的会员数
            active_with_booking_raw = await db.execute(
                select(func.count(func.distinct(Booking.member_id)))
                .join(CourseSchedule)
                .where(
                    Booking.organization_id == organization_id,
                    CourseSchedule.start_time >= now - timedelta(days=30),
                    Booking.status != BookingStatus.CANCELLED,
                )
            )
            active_with_booking = active_with_booking_raw.scalar() or 0
            at_risk_count = total_active_long - active_with_booking
            if at_risk_count > 0:
                alerts.append({
                    "type": "warning",
                    "title": "流失风险会员",
                    "message": f"有 {at_risk_count} 位活跃会员30天内无预约记录",
                    "count": at_risk_count,
                    "action_url": "/members?filter=at_risk",
                })

        # ========== 课程满课率过低 (近7天) ==========
        seven_days_ago = now - timedelta(days=7)
        low_fill_raw = await db.execute(
            select(func.count(CourseSchedule.id)).where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.start_time >= seven_days_ago,
                CourseSchedule.start_time < now,
                CourseSchedule.status != "cancelled",
                CourseSchedule.enrolled_count < 3,
            )
        )
        low_fill_count = low_fill_raw.scalar() or 0
        if low_fill_count > 0:
            alerts.append({
                "type": "info",
                "title": "低满课率课程",
                "message": f"近7天有 {low_fill_count} 节课程报名人数不足3人",
                "count": low_fill_count,
                "action_url": "/courses/schedules?filter=low_fill",
            })

        return alerts
