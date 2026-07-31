"""
ETL 服务 - 数据仓库预聚合
从 orders, members, bookings, course_schedules 等表聚合数据到预统计表
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_, or_, cast, Float as SAFloat
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.order import Order, OrderStatus
from backend.models.member import Member, MemberStatus
from backend.models.booking import Booking, BookingStatus
from backend.models.course import CourseSchedule, Course
from backend.models.coach import Coach
from backend.models.daily_stats import DailyStats
from backend.models.member_lifecycle import MemberLifecycleEvent
from backend.models.coach_stats import CoachDailyStats


class ETLService:
    """ETL 服务 - 数据抽取、转换、加载"""

    @staticmethod
    async def generate_daily_stats(
        db: AsyncSession,
        organization_id: int,
        stat_date: date,
        store_id: Optional[int] = None,
    ) -> dict:
        """
        生成每日统计数据
        - 从 orders, members, bookings, course_schedules 聚合数据
        - Upsert 到 daily_stats 表
        """
        day_start = datetime.combine(stat_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        # ========== 营收指标 ==========
        order_conditions = [
            Order.organization_id == organization_id,
            Order.payment_status == OrderStatus.PAID,
            Order.paid_at >= day_start,
            Order.paid_at < day_end,
        ]
        if store_id:
            order_conditions.append(Order.store_id == store_id)

        revenue_result = await db.execute(
            select(
                func.coalesce(func.sum(Order.actual_amount), 0),
                func.count(Order.id),
                func.coalesce(func.sum(Order.refund_amount), 0),
            ).where(*order_conditions)
        )
        revenue_row = revenue_result.one()
        total_revenue = float(revenue_row[0])
        order_count = int(revenue_row[1])
        refund_amount = float(revenue_row[2])
        avg_order_value = round(total_revenue / order_count, 2) if order_count > 0 else 0

        # 新会员营收 (当天注册当天购买的)
        new_member_conditions = list(order_conditions)
        new_member_conditions.append(Order.created_at >= day_start)
        new_member_conditions.append(Order.created_at < day_end)
        new_revenue_result = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0)).where(*new_member_conditions)
        )
        new_members_revenue = float(new_revenue_result.scalar() or 0)
        renewal_revenue = max(total_revenue - new_members_revenue, 0)

        # ========== 会员指标 ==========
        member_conditions = [Member.organization_id == organization_id]
        if store_id:
            member_conditions.append(Member.store_id == store_id)

        total_members_result = await db.execute(
            select(func.count(Member.id)).where(*member_conditions)
        )
        total_members = int(total_members_result.scalar() or 0)

        new_members_result = await db.execute(
            select(func.count(Member.id)).where(
                *member_conditions,
                Member.created_at >= day_start,
                Member.created_at < day_end,
            )
        )
        new_members = int(new_members_result.scalar() or 0)

        active_members_result = await db.execute(
            select(func.count(Member.id)).where(
                *member_conditions,
                Member.status == MemberStatus.ACTIVE,
            )
        )
        active_members = int(active_members_result.scalar() or 0)

        expired_members_result = await db.execute(
            select(func.count(Member.id)).where(
                *member_conditions,
                Member.status == MemberStatus.CANCELLED,
            )
        )
        expired_members = int(expired_members_result.scalar() or 0)

        frozen_members_result = await db.execute(
            select(func.count(Member.id)).where(
                *member_conditions,
                Member.status == MemberStatus.FROZEN,
            )
        )
        frozen_members = int(frozen_members_result.scalar() or 0)

        # ========== 预约指标 ==========
        booking_conditions = [
            Booking.organization_id == organization_id,
            Booking.created_at >= day_start,
            Booking.created_at < day_end,
        ]
        if store_id:
            booking_conditions.append(Booking.store_id == store_id)

        total_bookings_result = await db.execute(
            select(func.count(Booking.id)).where(*booking_conditions)
        )
        total_bookings = int(total_bookings_result.scalar() or 0)

        checked_in_result = await db.execute(
            select(func.count(Booking.id)).where(
                *booking_conditions,
                Booking.status == BookingStatus.CHECKED_IN,
            )
        )
        checked_in = int(checked_in_result.scalar() or 0)

        cancelled_result = await db.execute(
            select(func.count(Booking.id)).where(
                *booking_conditions,
                Booking.status == BookingStatus.CANCELLED,
            )
        )
        cancelled_bookings = int(cancelled_result.scalar() or 0)

        no_shows_result = await db.execute(
            select(func.count(Booking.id)).where(
                *booking_conditions,
                Booking.status == BookingStatus.NO_SHOW,
            )
        )
        no_shows = int(no_shows_result.scalar() or 0)

        effective_bookings = total_bookings - cancelled_bookings
        checkin_rate = round(checked_in / effective_bookings * 100, 1) if effective_bookings > 0 else 0

        # ========== 课程指标 ==========
        schedule_conditions = [
            CourseSchedule.organization_id == organization_id,
            CourseSchedule.start_time >= day_start,
            CourseSchedule.start_time < day_end,
            CourseSchedule.status != "cancelled",
        ]
        if store_id:
            schedule_conditions.append(CourseSchedule.store_id == store_id)

        total_classes_result = await db.execute(
            select(func.count(CourseSchedule.id)).where(*schedule_conditions)
        )
        total_classes = int(total_classes_result.scalar() or 0)

        # 平均满课率
        fill_rate_result = await db.execute(
            select(
                func.coalesce(
                    func.avg(
                        func.cast(CourseSchedule.enrolled_count, SAFloat)
                        / func.nullif(Course.max_attendees, 0)
                    ), 0
                )
            )
            .select_from(CourseSchedule)
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(*schedule_conditions)
        )
        avg_fill_rate = round(float(fill_rate_result.scalar() or 0) * 100, 1)

        # 最热门课程
        popular_course_result = await db.execute(
            select(
                Course.id,
                Course.name,
                func.count(Booking.id).label("booking_count"),
            )
            .select_from(CourseSchedule)
            .join(Course, CourseSchedule.course_id == Course.id)
            .outerjoin(Booking, Booking.schedule_id == CourseSchedule.id)
            .where(*schedule_conditions)
            .group_by(Course.id, Course.name)
            .order_by(func.count(Booking.id).desc())
            .limit(1)
        )
        popular_row = popular_course_result.first()
        popular_course_id = popular_row[0] if popular_row else None
        popular_course_name = popular_row[1] if popular_row else None

        # ========== 教练指标 ==========
        coach_conditions = [
            Coach.organization_id == organization_id,
            Coach.is_active == True,
        ]
        if store_id:
            coach_conditions.append(Coach.store_id == store_id)

        active_coaches_result = await db.execute(
            select(func.count(Coach.id)).where(*coach_conditions)
        )
        active_coaches = int(active_coaches_result.scalar() or 0)

        teaching_hours_result = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        (func.julianday(CourseSchedule.end_time) - func.julianday(CourseSchedule.start_time)) * 24
                    ), 0
                )
            )
            .select_from(CourseSchedule)
            .join(Course, CourseSchedule.course_id == Course.id)
            .join(Coach, Course.coach_id == Coach.id)
            .where(*schedule_conditions)
        )
        total_teaching_hours = round(float(teaching_hours_result.scalar() or 0), 2)

        # ========== Upsert ==========
        existing = await db.execute(
            select(DailyStats).where(
                DailyStats.organization_id == organization_id,
                DailyStats.stat_date == stat_date,
                DailyStats.store_id == store_id,
            )
        )
        stats_row = existing.scalar_one_or_none()

        if stats_row:
            # 更新
            stats_row.total_revenue = total_revenue
            stats_row.order_count = order_count
            stats_row.new_members_revenue = new_members_revenue
            stats_row.renewal_revenue = renewal_revenue
            stats_row.refund_amount = refund_amount
            stats_row.avg_order_value = avg_order_value
            stats_row.total_members = total_members
            stats_row.new_members = new_members
            stats_row.active_members = active_members
            stats_row.expired_members = expired_members
            stats_row.frozen_members = frozen_members
            stats_row.total_bookings = total_bookings
            stats_row.checked_in = checked_in
            stats_row.cancelled_bookings = cancelled_bookings
            stats_row.no_shows = no_shows
            stats_row.checkin_rate = checkin_rate
            stats_row.total_classes = total_classes
            stats_row.avg_fill_rate = avg_fill_rate
            stats_row.popular_course_id = popular_course_id
            stats_row.popular_course_name = popular_course_name
            stats_row.active_coaches = active_coaches
            stats_row.total_teaching_hours = total_teaching_hours
        else:
            # 新建
            stats_row = DailyStats(
                organization_id=organization_id,
                stat_date=stat_date,
                store_id=store_id,
                total_revenue=total_revenue,
                order_count=order_count,
                new_members_revenue=new_members_revenue,
                renewal_revenue=renewal_revenue,
                refund_amount=refund_amount,
                avg_order_value=avg_order_value,
                total_members=total_members,
                new_members=new_members,
                active_members=active_members,
                expired_members=expired_members,
                frozen_members=frozen_members,
                total_bookings=total_bookings,
                checked_in=checked_in,
                cancelled_bookings=cancelled_bookings,
                no_shows=no_shows,
                checkin_rate=checkin_rate,
                total_classes=total_classes,
                avg_fill_rate=avg_fill_rate,
                popular_course_id=popular_course_id,
                popular_course_name=popular_course_name,
                active_coaches=active_coaches,
                total_teaching_hours=total_teaching_hours,
            )
            db.add(stats_row)

        await db.flush()

        return {
            "stat_date": stat_date.isoformat(),
            "store_id": store_id,
            "total_revenue": total_revenue,
            "order_count": order_count,
            "total_members": total_members,
            "new_members": new_members,
            "active_members": active_members,
            "total_bookings": total_bookings,
            "checked_in": checked_in,
            "total_classes": total_classes,
        }

    @staticmethod
    async def generate_member_lifecycle_events(
        db: AsyncSession,
        organization_id: int,
        event_date: date,
    ) -> dict:
        """
        检测并记录会员生命周期事件
        - 新注册会员
        - 首次到店
        - 卡购买/续费/到期
        - 流失（N天无活动）
        """
        day_start = datetime.combine(event_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        events_created = 0

        # 1. 新注册会员
        new_members_result = await db.execute(
            select(Member.id, Member.store_id).where(
                Member.organization_id == organization_id,
                Member.created_at >= day_start,
                Member.created_at < day_end,
            )
        )
        for member_id, member_store_id in new_members_result:
            event = MemberLifecycleEvent(
                organization_id=organization_id,
                member_id=member_id,
                store_id=member_store_id,
                event_type="register",
                event_date=event_date,
                event_data={"source": "registration"},
            )
            db.add(event)
            events_created += 1

        # 2. 首次到店 (有签到记录的会员，之前没有签到记录)
        checked_in_members = await db.execute(
            select(Booking.member_id)
            .where(
                Booking.organization_id == organization_id,
                Booking.status == BookingStatus.CHECKED_IN,
                Booking.check_in_time >= day_start,
                Booking.check_in_time < day_end,
            )
            .distinct()
        )
        for (member_id,) in checked_in_members:
            # 检查之前是否有签到记录
            prev_checkin = await db.execute(
                select(func.count(Booking.id)).where(
                    Booking.member_id == member_id,
                    Booking.status == BookingStatus.CHECKED_IN,
                    Booking.check_in_time < day_start,
                )
            )
            if int(prev_checkin.scalar() or 0) == 0:
                member_info = await db.execute(
                    select(Member.store_id).where(Member.id == member_id)
                )
                member_store_id = member_info.scalar()
                event = MemberLifecycleEvent(
                    organization_id=organization_id,
                    member_id=member_id,
                    store_id=member_store_id,
                    event_type="first_visit",
                    event_date=event_date,
                    event_data={"source": "check_in"},
                )
                db.add(event)
                events_created += 1

        # 3. 卡到期检测
        expired_members = await db.execute(
            select(Member.id, Member.store_id).where(
                Member.organization_id == organization_id,
                Member.card_end_date >= day_start,
                Member.card_end_date < day_end,
                Member.status == MemberStatus.ACTIVE,
            )
        )
        for member_id, member_store_id in expired_members:
            event = MemberLifecycleEvent(
                organization_id=organization_id,
                member_id=member_id,
                store_id=member_store_id,
                event_type="card_expire",
                event_date=event_date,
                event_data={"source": "auto_detect"},
            )
            db.add(event)
            events_created += 1

        # 4. 冻结/解冻事件
        frozen_members = await db.execute(
            select(Member.id, Member.store_id).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.FROZEN,
                Member.updated_at >= day_start,
                Member.updated_at < day_end,
            )
        )
        for member_id, member_store_id in frozen_members:
            event = MemberLifecycleEvent(
                organization_id=organization_id,
                member_id=member_id,
                store_id=member_store_id,
                event_type="freeze",
                event_date=event_date,
                event_data={"source": "status_change"},
            )
            db.add(event)
            events_created += 1

        # 5. 流失检测 (30天无活动的活跃会员)
        churn_threshold = day_start - timedelta(days=30)
        active_members = await db.execute(
            select(Member.id, Member.store_id).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
            )
        )
        for member_id, member_store_id in active_members:
            # 检查最近30天是否有活动
            recent_booking = await db.execute(
                select(func.count(Booking.id)).where(
                    Booking.member_id == member_id,
                    Booking.created_at >= churn_threshold,
                )
            )
            recent_order = await db.execute(
                select(func.count(Order.id)).where(
                    Order.member_id == member_id,
                    Order.created_at >= churn_threshold,
                )
            )
            if int(recent_booking.scalar() or 0) == 0 and int(recent_order.scalar() or 0) == 0:
                # 检查是否已经有 churn 事件
                existing_churn = await db.execute(
                    select(func.count(MemberLifecycleEvent.id)).where(
                        MemberLifecycleEvent.member_id == member_id,
                        MemberLifecycleEvent.event_type == "churn",
                    )
                )
                if int(existing_churn.scalar() or 0) == 0:
                    event = MemberLifecycleEvent(
                        organization_id=organization_id,
                        member_id=member_id,
                        store_id=member_store_id,
                        event_type="churn",
                        event_date=event_date,
                        event_data={"source": "auto_detect", "inactive_days": 30},
                    )
                    db.add(event)
                    events_created += 1

        await db.flush()

        return {
            "event_date": event_date.isoformat(),
            "events_created": events_created,
        }

    @staticmethod
    async def generate_coach_daily_stats(
        db: AsyncSession,
        organization_id: int,
        stat_date: date,
    ) -> dict:
        """
        生成教练每日统计
        """
        day_start = datetime.combine(stat_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        # 获取当天有排期的教练
        coach_stats_data = await db.execute(
            select(
                Coach.id.label("coach_id"),
                Coach.store_id.label("store_id"),
                func.count(CourseSchedule.id).label("classes_taught"),
                func.coalesce(func.sum(CourseSchedule.enrolled_count), 0).label("total_students"),
                func.coalesce(
                    func.sum(
                        (func.julianday(CourseSchedule.end_time) - func.julianday(CourseSchedule.start_time)) * 24
                    ), 0
                ).label("total_hours"),
            )
            .select_from(Coach)
            .join(Course, Course.coach_id == Coach.id)
            .join(CourseSchedule, CourseSchedule.course_id == Course.id)
            .where(
                Coach.organization_id == organization_id,
                CourseSchedule.start_time >= day_start,
                CourseSchedule.start_time < day_end,
                CourseSchedule.status != "cancelled",
            )
            .group_by(Coach.id, Coach.store_id)
        )

        coaches_processed = 0
        for row in coach_stats_data:
            coach_id = row.coach_id
            store_id = row.store_id
            classes_taught = int(row.classes_taught)
            total_students = int(row.total_students)
            total_hours = round(float(row.total_hours), 2)

            # 新学员数 (当天首次预约该教练的学员)
            new_students_result = await db.execute(
                select(func.count(func.distinct(Booking.member_id)))
                .select_from(CourseSchedule)
                .join(Booking, Booking.schedule_id == CourseSchedule.id)
                .join(Course, CourseSchedule.course_id == Course.id)
                .where(
                    Course.coach_id == coach_id,
                    CourseSchedule.start_time >= day_start,
                    CourseSchedule.start_time < day_end,
                    Booking.status != BookingStatus.CANCELLED,
                )
                .where(
                    Booking.member_id.notin_(
                        select(Booking.member_id)
                        .select_from(CourseSchedule)
                        .join(Booking, Booking.schedule_id == CourseSchedule.id)
                        .join(Course, CourseSchedule.course_id == Course.id)
                        .where(
                            Course.coach_id == coach_id,
                            CourseSchedule.start_time < day_start,
                        )
                    )
                )
            )
            new_students = int(new_students_result.scalar() or 0)

            # 营收贡献 (当天该教练课程的订单)
            revenue_result = await db.execute(
                select(func.coalesce(func.sum(Order.actual_amount), 0))
                .join(CourseSchedule, Order.product_id == CourseSchedule.id)
                .join(Course, CourseSchedule.course_id == Course.id)
                .where(
                    Course.coach_id == coach_id,
                    Order.organization_id == organization_id,
                    Order.payment_status == OrderStatus.PAID,
                    Order.paid_at >= day_start,
                    Order.paid_at < day_end,
                )
            )
            revenue_contribution = float(revenue_result.scalar() or 0)

            # Upsert
            existing = await db.execute(
                select(CoachDailyStats).where(
                    CoachDailyStats.organization_id == organization_id,
                    CoachDailyStats.coach_id == coach_id,
                    CoachDailyStats.stat_date == stat_date,
                )
            )
            coach_stat = existing.scalar_one_or_none()

            if coach_stat:
                coach_stat.classes_taught = classes_taught
                coach_stat.total_students = total_students
                coach_stat.total_hours = total_hours
                coach_stat.new_students = new_students
                coach_stat.revenue_contribution = revenue_contribution
            else:
                coach_stat = CoachDailyStats(
                    organization_id=organization_id,
                    coach_id=coach_id,
                    store_id=store_id,
                    stat_date=stat_date,
                    classes_taught=classes_taught,
                    total_students=total_students,
                    total_hours=total_hours,
                    new_students=new_students,
                    revenue_contribution=revenue_contribution,
                )
                db.add(coach_stat)

            coaches_processed += 1

        await db.flush()

        return {
            "stat_date": stat_date.isoformat(),
            "coaches_processed": coaches_processed,
        }

    @staticmethod
    async def backfill_stats(
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        回填历史统计数据
        - 逐日生成 daily_stats
        - 返回处理进度
        """
        total_days = (end_date - start_date).days + 1
        processed = 0
        errors = 0

        current_date = start_date
        while current_date <= end_date:
            try:
                await ETLService.generate_daily_stats(
                    db, organization_id, current_date
                )
                processed += 1
            except Exception as e:
                errors += 1
            current_date += timedelta(days=1)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days": total_days,
            "processed": processed,
            "errors": errors,
        }

    @staticmethod
    async def get_member_retention_cohorts(
        db: AsyncSession,
        organization_id: int,
    ) -> list[dict]:
        """
        会员留存分析 - 按注册月份分组
        - 返回每月注册的会员在第1/2/3...月的留存率
        """
        # Step 1: Get all members with their cohort month (1 query)
        member_rows = await db.execute(
            select(
                Member.id,
                func.strftime('%Y-%m', Member.created_at).label("cohort_month"),
            )
            .where(Member.organization_id == organization_id)
        )
        member_cohorts = {}  # cohort_month -> [member_id, ...]
        for row in member_rows:
            cm = row.cohort_month
            if cm not in member_cohorts:
                member_cohorts[cm] = []
            member_cohorts[cm].append(row.id)

        if not member_cohorts:
            return []

        # Determine the broad date range needed
        cohort_months = sorted(member_cohorts.keys())
        earliest_cohort = datetime.strptime(cohort_months[0], "%Y-%m")
        latest_target = datetime.strptime(cohort_months[-1], "%Y-%m") + timedelta(days=32 * 13)

        # Step 2: Get all bookings and orders in the date range (2 queries)
        booking_rows = await db.execute(
            select(Booking.member_id, Booking.created_at)
            .where(
                Booking.organization_id == organization_id,
                Booking.created_at >= earliest_cohort,
                Booking.created_at < latest_target,
            )
        )
        order_rows = await db.execute(
            select(Order.member_id, Order.created_at)
            .where(
                Order.organization_id == organization_id,
                Order.created_at >= earliest_cohort,
                Order.created_at < latest_target,
            )
        )

        # Build lookup: member_id -> set of (year, month) tuples with activity
        from collections import defaultdict
        active_months: dict[int, set[tuple[int, int]]] = defaultdict(set)
        for row in booking_rows:
            active_months[row.member_id].add((row.created_at.year, row.created_at.month))
        for row in order_rows:
            active_months[row.member_id].add((row.created_at.year, row.created_at.month))

        # Step 3: Compute retention per cohort in Python
        result = []
        for cm in cohort_months:
            member_ids = member_cohorts[cm]
            cohort_size = len(member_ids)
            cohort_date = datetime.strptime(cm, "%Y-%m")
            cohort_data = {
                "cohort_month": cm,
                "cohort_size": cohort_size,
                "retention": [],
            }

            for offset in range(1, 13):
                target_date = cohort_date + timedelta(days=32 * offset)
                target_year, target_month = target_date.year, target_date.month

                active_count = sum(
                    1 for mid in member_ids
                    if (target_year, target_month) in active_months.get(mid, set())
                )
                retention_rate = round(active_count / cohort_size * 100, 1) if cohort_size > 0 else 0
                cohort_data["retention"].append({
                    "month": offset,
                    "active_count": active_count,
                    "retention_rate": retention_rate,
                })

            result.append(cohort_data)

        return result

    @staticmethod
    async def get_member_lifetime_value(
        db: AsyncSession,
        organization_id: int,
    ) -> dict:
        """
        会员生命周期价值分析
        - 平均LTV
        - 按会员等级/卡类型的LTV分布
        """
        # 总体LTV
        ltv_result = await db.execute(
            select(
                func.coalesce(func.avg(Member.total_consumption), 0),
                func.coalesce(func.sum(Member.total_consumption), 0),
                func.count(Member.id),
            ).where(Member.organization_id == organization_id)
        )
        ltv_row = ltv_result.one()
        avg_ltv = round(float(ltv_row[0]), 2)
        total_ltv = round(float(ltv_row[1]), 2)
        total_members = int(ltv_row[2])

        # 按等级分布
        level_dist_result = await db.execute(
            select(
                Member.level,
                func.count(Member.id).label("count"),
                func.coalesce(func.avg(Member.total_consumption), 0).label("avg_ltv"),
            )
            .where(Member.organization_id == organization_id)
            .group_by(Member.level)
            .order_by(Member.level)
        )
        by_level = [
            {
                "level": row.level,
                "count": int(row.count),
                "avg_ltv": round(float(row.avg_ltv), 2),
            }
            for row in level_dist_result
        ]

        # 按卡类型分布
        card_dist_result = await db.execute(
            select(
                Member.card_type,
                func.count(Member.id).label("count"),
                func.coalesce(func.avg(Member.total_consumption), 0).label("avg_ltv"),
            )
            .where(Member.organization_id == organization_id)
            .group_by(Member.card_type)
        )
        by_card_type = [
            {
                "card_type": row.card_type,
                "count": int(row.count),
                "avg_ltv": round(float(row.avg_ltv), 2),
            }
            for row in card_dist_result
        ]

        return {
            "avg_ltv": avg_ltv,
            "total_ltv": total_ltv,
            "total_members": total_members,
            "by_level": by_level,
            "by_card_type": by_card_type,
        }

    @staticmethod
    async def get_churn_analysis(
        db: AsyncSession,
        organization_id: int,
    ) -> dict:
        """
        流失分析
        - 流失率趋势
        - 流失原因分布
        - 高风险会员列表
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # 总体流失率
        total_members_result = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
            )
        )
        total_members = int(total_members_result.scalar() or 0)

        churned_result = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.CANCELLED,
            )
        )
        churned_count = int(churned_result.scalar() or 0)
        churn_rate = round(churned_count / total_members * 100, 1) if total_members > 0 else 0

        # 流失事件分布
        churn_events_result = await db.execute(
            select(
                func.coalesce(MemberLifecycleEvent.event_data, "{}").label("event_data"),
                func.count(MemberLifecycleEvent.id).label("count"),
            )
            .where(
                MemberLifecycleEvent.organization_id == organization_id,
                MemberLifecycleEvent.event_type == "churn",
            )
            .group_by(MemberLifecycleEvent.event_data)
        )
        churn_reasons = [
            {"reason": "inactive_30d", "count": int(row.count)}
            for row in churn_events_result
        ]

        # 高风险会员 (活跃但30天无活动)
        churn_threshold = now - timedelta(days=30)
        at_risk_result = await db.execute(
            select(
                Member.id,
                Member.name,
                Member.phone,
                Member.card_type,
                Member.total_consumption,
                Member.created_at,
            )
            .where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
            )
            .order_by(Member.total_consumption.desc())
        )

        at_risk_members = []
        for row in at_risk_result:
            member_id = row.id
            # 检查最近30天是否有活动
            recent_booking = await db.execute(
                select(func.count(Booking.id)).where(
                    Booking.member_id == member_id,
                    Booking.created_at >= churn_threshold,
                )
            )
            recent_order = await db.execute(
                select(func.count(Order.id)).where(
                    Order.member_id == member_id,
                    Order.created_at >= churn_threshold,
                )
            )
            if int(recent_booking.scalar() or 0) == 0 and int(recent_order.scalar() or 0) == 0:
                at_risk_members.append({
                    "id": member_id,
                    "name": row.name,
                    "phone": row.phone,
                    "card_type": row.card_type,
                    "total_consumption": float(row.total_consumption),
                    "member_since": row.created_at.isoformat() if row.created_at else None,
                })

        # 按月流失趋势 (最近6个月)
        churn_trend = []
        for month_offset in range(6):
            month_start = (now - timedelta(days=30 * (month_offset + 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (now - timedelta(days=30 * month_offset)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            churned_in_month = await db.execute(
                select(func.count(MemberLifecycleEvent.id)).where(
                    MemberLifecycleEvent.organization_id == organization_id,
                    MemberLifecycleEvent.event_type == "churn",
                    MemberLifecycleEvent.event_date >= month_start.date(),
                    MemberLifecycleEvent.event_date < month_end.date(),
                )
            )
            churn_trend.append({
                "month": month_start.strftime("%Y-%m"),
                "churned_count": int(churned_in_month.scalar() or 0),
            })

        return {
            "total_members": total_members,
            "churned_count": churned_count,
            "churn_rate": churn_rate,
            "churn_reasons": churn_reasons,
            "at_risk_members": at_risk_members[:50],  # 最多返回50个
            "churn_trend": list(reversed(churn_trend)),
        }
