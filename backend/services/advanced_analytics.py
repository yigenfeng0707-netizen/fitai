"""高级数据分析服务 - 核心指标报表"""
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, case, text, Float as SAFloat
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.order import Order, OrderStatus
from backend.models.member import Member, MemberStatus, CardType
from backend.models.booking import Booking, BookingStatus
from backend.models.course import CourseSchedule, Course, CourseType
from backend.models.coach import Coach
from backend.models.store import Store
from backend.models.lead import Lead, LeadStatus


class AdvancedAnalyticsService:
    """高级数据分析服务"""

    @staticmethod
    async def get_revenue_analysis(
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
        group_by: str = "day",
        store_id: Optional[int] = None,
    ) -> dict:
        """
        营收分析
        - 总营收、订单数、平均客单价
        - 按时间维度分组趋势
        - 收入构成（新购/续费/其他）
        - 同比/环比增长
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # 前一周期（用于环比计算）
        period_days = (end_date - start_date).days + 1
        prev_start_dt = start_dt - timedelta(days=period_days)
        prev_end_dt = start_dt - timedelta(seconds=1)

        # 基础过滤条件
        base_filters = [
            Order.organization_id == organization_id,
            Order.payment_status == OrderStatus.PAID,
            Order.paid_at >= start_dt,
            Order.paid_at <= end_dt,
        ]
        if store_id:
            base_filters.append(Order.store_id == store_id)

        # ========== 概览 ==========
        # 总营收
        total_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(*base_filters)
        )
        total_revenue = float(total_revenue_raw.scalar() or 0)

        # 订单数
        order_count_raw = await db.execute(
            select(func.count(Order.id)).where(*base_filters)
        )
        order_count = order_count_raw.scalar() or 0

        # 退款金额
        refund_filters = [
            Order.organization_id == organization_id,
            Order.payment_status == OrderStatus.REFUNDED,
            Order.refunded_at >= start_dt,
            Order.refunded_at <= end_dt,
        ]
        if store_id:
            refund_filters.append(Order.store_id == store_id)
        refund_raw = await db.execute(
            select(func.coalesce(func.sum(Order.refund_amount), 0))
            .where(*refund_filters)
        )
        refund_amount = float(refund_raw.scalar() or 0)

        # 净营收
        net_revenue = total_revenue - refund_amount

        # 平均客单价
        avg_order_value = round(total_revenue / order_count, 2) if order_count > 0 else 0.0

        # 环比增长率
        prev_filters = [
            Order.organization_id == organization_id,
            Order.payment_status == OrderStatus.PAID,
            Order.paid_at >= prev_start_dt,
            Order.paid_at <= prev_end_dt,
        ]
        if store_id:
            prev_filters.append(Order.store_id == store_id)
        prev_revenue_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(*prev_filters)
        )
        prev_revenue = float(prev_revenue_raw.scalar() or 0)
        growth_rate = round(
            ((total_revenue - prev_revenue) / prev_revenue * 100), 1
        ) if prev_revenue > 0 else 0.0

        overview = {
            "total_revenue": total_revenue,
            "order_count": order_count,
            "avg_order_value": avg_order_value,
            "refund_amount": refund_amount,
            "net_revenue": net_revenue,
            "growth_rate": growth_rate,
        }

        # ========== 趋势 ==========
        trend = await AdvancedAnalyticsService._build_revenue_trend(
            db, organization_id, start_date, end_date, group_by, store_id
        )

        # ========== 收入构成 ==========
        # 根据 subject 关键字推断收入类型
        new_purchase_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(*base_filters, Order.subject.contains("新购"))
        )
        new_purchase = float(new_purchase_raw.scalar() or 0)

        renewal_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(*base_filters, Order.subject.contains("续费"))
        )
        renewal = float(renewal_raw.scalar() or 0)

        upgrade_raw = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(*base_filters, Order.subject.contains("升级"))
        )
        upgrade = float(upgrade_raw.scalar() or 0)

        other = max(0, total_revenue - new_purchase - renewal - upgrade)

        composition = {
            "new_purchase": new_purchase,
            "renewal": renewal,
            "upgrade": upgrade,
            "other": other,
        }

        # ========== 热门商品 ==========
        top_products_query = (
            select(
                Order.subject,
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.actual_amount), 0).label("total_amount"),
            )
            .where(*base_filters)
            .group_by(Order.subject)
            .order_by(func.sum(Order.actual_amount).desc())
            .limit(10)
        )
        top_products_result = await db.execute(top_products_query)
        top_products = [
            {
                "subject": row.subject or "未分类",
                "order_count": row.order_count,
                "total_amount": float(row.total_amount),
            }
            for row in top_products_result
        ]

        return {
            "overview": overview,
            "trend": trend,
            "composition": composition,
            "top_products": top_products,
        }

    @staticmethod
    async def _build_revenue_trend(
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
        group_by: str,
        store_id: Optional[int] = None,
    ) -> list[dict]:
        """构建营收趋势数据"""
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        base_filters = [
            Order.organization_id == organization_id,
            Order.payment_status == OrderStatus.PAID,
            Order.paid_at >= start_dt,
            Order.paid_at <= end_dt,
        ]
        if store_id:
            base_filters.append(Order.store_id == store_id)

        if group_by == "day":
            rows = await db.execute(
                select(
                    func.date(Order.paid_at).label("period"),
                    func.coalesce(func.sum(Order.actual_amount), 0).label("revenue"),
                    func.count(Order.id).label("order_count"),
                )
                .where(*base_filters)
                .group_by(func.date(Order.paid_at))
                .order_by(func.date(Order.paid_at))
            )
            data_map = {}
            for r in rows:
                key = str(r.period)
                data_map[key] = {
                    "period": key,
                    "revenue": float(r.revenue),
                    "order_count": r.order_count,
                    "avg_order_value": round(float(r.revenue) / r.order_count, 2) if r.order_count > 0 else 0.0,
                }
            # 填充缺失日期
            trend = []
            current = start_date
            while current <= end_date:
                key = str(current)
                if key in data_map:
                    trend.append(data_map[key])
                else:
                    trend.append({
                        "period": key,
                        "revenue": 0.0,
                        "order_count": 0,
                        "avg_order_value": 0.0,
                    })
                current += timedelta(days=1)
            return trend

        elif group_by == "week":
            rows = await db.execute(
                select(
                    func.date(Order.paid_at).label("period"),
                    func.coalesce(func.sum(Order.actual_amount), 0).label("revenue"),
                    func.count(Order.id).label("order_count"),
                )
                .where(*base_filters)
                .group_by(func.date(Order.paid_at))
                .order_by(func.date(Order.paid_at))
            )
            # 按周聚合
            week_map: dict[str, dict] = {}
            for r in rows:
                d = r.period if isinstance(r.period, date) else date.fromisoformat(str(r.period))
                week_start = d - timedelta(days=d.weekday())
                key = str(week_start)
                if key not in week_map:
                    week_map[key] = {"period": key, "revenue": 0.0, "order_count": 0}
                week_map[key]["revenue"] += float(r.revenue)
                week_map[key]["order_count"] += r.order_count
            trend = []
            for k in sorted(week_map.keys()):
                item = week_map[k]
                item["avg_order_value"] = round(item["revenue"] / item["order_count"], 2) if item["order_count"] > 0 else 0.0
                trend.append(item)
            return trend

        else:  # month
            rows = await db.execute(
                select(
                    func.strftime("%Y-%m", Order.paid_at).label("period"),
                    func.coalesce(func.sum(Order.actual_amount), 0).label("revenue"),
                    func.count(Order.id).label("order_count"),
                )
                .where(*base_filters)
                .group_by(func.strftime("%Y-%m", Order.paid_at))
                .order_by(func.strftime("%Y-%m", Order.paid_at))
            )
            trend = []
            for r in rows:
                trend.append({
                    "period": str(r.period),
                    "revenue": float(r.revenue),
                    "order_count": r.order_count,
                    "avg_order_value": round(float(r.revenue) / r.order_count, 2) if r.order_count > 0 else 0.0,
                })
            return trend

    @staticmethod
    async def get_member_analysis(
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
        store_id: Optional[int] = None,
    ) -> dict:
        """
        会员分析
        - 新增/活跃/流失会员趋势
        - 会员等级分布
        - 卡类型分布
        - 会员来源分析
        - 平均消费金额
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # ========== 概览 ==========
        member_base = [Member.organization_id == organization_id]
        if store_id:
            member_base.append(Member.store_id == store_id)

        # 总会员数
        total_raw = await db.execute(select(func.count(Member.id)).where(*member_base))
        total_members = total_raw.scalar() or 0

        # 新增会员（期间内创建）
        new_filters = member_base + [Member.created_at >= start_dt, Member.created_at <= end_dt]
        new_raw = await db.execute(select(func.count(Member.id)).where(*new_filters))
        new_members = new_raw.scalar() or 0

        # 活跃会员
        active_raw = await db.execute(
            select(func.count(Member.id)).where(*member_base, Member.status == MemberStatus.ACTIVE)
        )
        active_members = active_raw.scalar() or 0

        # 流失会员（cancelled 状态）
        churned_raw = await db.execute(
            select(func.count(Member.id)).where(*member_base, Member.status == MemberStatus.CANCELLED)
        )
        churned_members = churned_raw.scalar() or 0

        net_growth = new_members - churned_members

        # 增长率：与上一周期对比
        period_days = (end_date - start_date).days + 1
        prev_start_dt = start_dt - timedelta(days=period_days)
        prev_end_dt = start_dt - timedelta(seconds=1)
        prev_new_filters = member_base + [Member.created_at >= prev_start_dt, Member.created_at <= prev_end_dt]
        prev_new_raw = await db.execute(select(func.count(Member.id)).where(*prev_new_filters))
        prev_new = prev_new_raw.scalar() or 0
        growth_rate = round(((new_members - prev_new) / prev_new * 100), 1) if prev_new > 0 else 0.0

        overview = {
            "total_members": total_members,
            "new_members": new_members,
            "active_members": active_members,
            "churned_members": churned_members,
            "net_growth": net_growth,
            "growth_rate": growth_rate,
        }

        # ========== 趋势（按日新增） ==========
        trend_rows = await db.execute(
            select(
                func.date(Member.created_at).label("date"),
                func.count(Member.id).label("count"),
            )
            .where(*new_filters)
            .group_by(func.date(Member.created_at))
            .order_by(func.date(Member.created_at))
        )
        trend_map = {str(r.date): r.count for r in trend_rows}
        trend = []
        current = start_date
        while current <= end_date:
            key = str(current)
            trend.append({"date": key, "new_count": trend_map.get(key, 0)})
            current += timedelta(days=1)

        # ========== 分布 ==========
        # 等级分布
        level_rows = await db.execute(
            select(Member.level, func.count(Member.id))
            .where(*member_base)
            .group_by(Member.level)
        )
        by_level = {str(r.level): r.count for r in level_rows}

        # 卡类型分布
        card_rows = await db.execute(
            select(Member.card_type, func.count(Member.id))
            .where(*member_base)
            .group_by(Member.card_type)
        )
        by_card_type = {str(r.card_type.value if r.card_type else "unknown"): r.count for r in card_rows}

        # 来源分布（从潜客转化来的会员）
        from backend.models.lead import Lead, LeadSource
        source_rows = await db.execute(
            select(Lead.source, func.count(Lead.id))
            .where(
                Lead.organization_id == organization_id,
                Lead.status == LeadStatus.CONVERTED,
                Lead.converted_member_id.isnot(None),
                Lead.created_at >= start_dt,
                Lead.created_at <= end_dt,
            )
            .group_by(Lead.source)
        )
        by_source = {str(r.source.value if r.source else "unknown"): r.count for r in source_rows}

        # 门店分布
        store_rows = await db.execute(
            select(Store.name, func.count(Member.id))
            .join(Member, Member.store_id == Store.id)
            .where(
                Member.organization_id == organization_id,
                Store.organization_id == organization_id,
            )
            .group_by(Store.id, Store.name)
        )
        by_store = [{"store_name": r.name, "count": r.count} for r in store_rows]

        distribution = {
            "by_level": by_level,
            "by_card_type": by_card_type,
            "by_source": by_source,
            "by_store": by_store,
        }

        # ========== 平均消费 ==========
        avg_consumption_raw = await db.execute(
            select(func.coalesce(func.avg(Member.total_consumption), 0))
            .where(*member_base)
        )
        avg_consumption = round(float(avg_consumption_raw.scalar() or 0), 2)

        return {
            "overview": overview,
            "trend": trend,
            "distribution": distribution,
            "avg_consumption": avg_consumption,
        }

    @staticmethod
    async def get_course_analysis(
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
        store_id: Optional[int] = None,
    ) -> dict:
        """
        课程分析
        - 课程热度排行
        - 满课率统计
        - 时段分布
        - 课程类型占比
        - 教练课时段分布
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        schedule_filters = [
            CourseSchedule.organization_id == organization_id,
            CourseSchedule.start_time >= start_dt,
            CourseSchedule.start_time <= end_dt,
            CourseSchedule.status != "cancelled",
        ]
        if store_id:
            schedule_filters.append(CourseSchedule.store_id == store_id)

        booking_filters = [
            Booking.organization_id == organization_id,
            Booking.status != BookingStatus.CANCELLED,
        ]

        # ========== 热门课程排行 ==========
        top_courses_query = (
            select(
                Course.name,
                Course.course_type,
                func.count(Booking.id).label("booking_count"),
                func.coalesce(func.sum(CourseSchedule.enrolled_count), 0).label("total_enrolled"),
                func.coalesce(func.sum(Course.max_attendees), 0).label("total_capacity"),
            )
            .select_from(CourseSchedule)
            .join(Course, CourseSchedule.course_id == Course.id)
            .outerjoin(Booking, Booking.schedule_id == CourseSchedule.id)
            .where(*schedule_filters)
            .group_by(Course.id, Course.name, Course.course_type, Course.max_attendees)
            .order_by(func.count(Booking.id).desc())
            .limit(10)
        )
        top_courses_result = await db.execute(top_courses_query)
        top_courses = []
        for r in top_courses_result:
            fill_rate = round((r.total_enrolled / r.total_capacity * 100), 1) if r.total_capacity > 0 else 0.0
            top_courses.append({
                "name": r.name,
                "course_type": r.course_type.value if r.course_type else "unknown",
                "booking_count": r.booking_count,
                "fill_rate": fill_rate,
            })

        # ========== 课程类型占比 ==========
        type_rows = await db.execute(
            select(Course.course_type, func.count(CourseSchedule.id).label("schedule_count"))
            .select_from(CourseSchedule)
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(*schedule_filters)
            .group_by(Course.course_type)
        )
        type_distribution = {
            str(r.course_type.value if r.course_type else "unknown"): r.schedule_count
            for r in type_rows
        }

        # ========== 时段分布 ==========
        bind = db.get_bind()
        dialect_name = bind.dialect.name if bind else "sqlite"
        if dialect_name == "sqlite":
            hour_sql = "strftime('%H', cs.start_time)"
        else:
            hour_sql = "to_char(cs.start_time, 'HH24')"

        hour_rows = await db.execute(
            text(f"""
                SELECT {hour_sql} AS hour, COUNT(b.id) AS count
                FROM course_schedules cs
                LEFT JOIN bookings b ON b.schedule_id = cs.id AND b.status != 'CANCELLED'
                WHERE cs.organization_id = :org_id
                  AND cs.start_time >= :start
                  AND cs.start_time <= :end
                  AND cs.status != 'cancelled'
                GROUP BY hour
                ORDER BY hour
            """),
            {"org_id": organization_id, "start": start_dt, "end": end_dt},
        )
        count_by_hour = {int(str(r[0])): int(r[1]) for r in hour_rows}
        time_slot_distribution = [
            {"hour": f"{h}:00", "count": count_by_hour.get(h, 0)}
            for h in range(6, 22)
        ]

        # ========== 平均满课率 ==========
        fill_rate_rows = await db.execute(
            select(
                CourseSchedule.enrolled_count,
                Course.max_attendees,
            )
            .select_from(CourseSchedule)
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(*schedule_filters)
        )
        fill_rates = []
        for r in fill_rate_rows:
            if r.max_attendees and r.max_attendees > 0:
                fill_rates.append(r.enrolled_count / r.max_attendees * 100)
        avg_fill_rate = round(sum(fill_rates) / len(fill_rates), 1) if fill_rates else 0.0

        return {
            "top_courses": top_courses,
            "type_distribution": type_distribution,
            "time_slot_distribution": time_slot_distribution,
            "avg_fill_rate": avg_fill_rate,
        }

    @staticmethod
    async def get_coach_performance_analysis(
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
        store_id: Optional[int] = None,
    ) -> list[dict]:
        """
        教练绩效分析
        - 课时排行
        - 学员满意度排行
        - 营收贡献排行
        - 教练利用率
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Fetch all active coaches
        coaches_result = await db.execute(
            select(Coach.id, Coach.name, Coach.avg_rating).where(
                Coach.organization_id == organization_id,
                Coach.is_active.is_(True),
            )
        )
        coaches = [(r.id, r.name, r.avg_rating) for r in coaches_result]

        if not coaches:
            return []

        # Batch: class counts per coach
        schedule_filters = [
            CourseSchedule.organization_id == organization_id,
            CourseSchedule.start_time >= start_dt,
            CourseSchedule.start_time <= end_dt,
            CourseSchedule.status != "cancelled",
        ]
        if store_id:
            schedule_filters.append(CourseSchedule.store_id == store_id)

        classes_rows = await db.execute(
            select(
                Course.coach_id,
                func.count(CourseSchedule.id).label("class_count"),
            )
            .select_from(CourseSchedule)
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(Course.coach_id.in_([c[0] for c in coaches]), *schedule_filters)
            .group_by(Course.coach_id)
        )
        classes_map = {r.coach_id: r.class_count for r in classes_rows}

        # Batch: distinct student counts per coach
        students_rows = await db.execute(
            select(
                Course.coach_id,
                func.count(func.distinct(Booking.member_id)).label("student_count"),
            )
            .select_from(Booking)
            .join(CourseSchedule, Booking.schedule_id == CourseSchedule.id)
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(
                Course.coach_id.in_([c[0] for c in coaches]),
                Booking.status != BookingStatus.CANCELLED,
                *schedule_filters,
            )
            .group_by(Course.coach_id)
        )
        students_map = {r.coach_id: r.student_count for r in students_rows}

        # Batch: revenue contribution per coach
        revenue_rows = await db.execute(
            select(
                Course.coach_id,
                func.coalesce(func.sum(Order.actual_amount), 0).label("revenue"),
            )
            .select_from(Order)
            .join(Course, Order.product_id == Course.id)
            .where(
                Course.coach_id.in_([c[0] for c in coaches]),
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= start_dt,
                Order.paid_at <= end_dt,
            )
            .group_by(Course.coach_id)
        )
        revenue_map = {r.coach_id: float(r.revenue) for r in revenue_rows}

        # Store name (single query if filtering by store)
        store_name = None
        if store_id:
            store_result = await db.execute(
                select(Store.name).where(Store.id == store_id)
            )
            store_name = store_result.scalar()

        # Utilization parameters
        period_days = (end_date - start_date).days + 1
        work_days = max(1, period_days * 5 // 7)
        max_capacity = work_days * 6

        results = []
        for coach_id, coach_name, avg_rating in coaches:
            classes_taught = classes_map.get(coach_id, 0)
            total_students = students_map.get(coach_id, 0)
            revenue_contribution = revenue_map.get(coach_id, 0.0)
            utilization_rate = round((classes_taught / max_capacity * 100), 1) if max_capacity > 0 else 0.0

            results.append({
                "coach_id": coach_id,
                "coach_name": coach_name,
                "store_name": store_name,
                "classes_taught": classes_taught,
                "total_students": total_students,
                "avg_rating": round(float(avg_rating or 0), 1),
                "revenue_contribution": revenue_contribution,
                "utilization_rate": utilization_rate,
            })

        results.sort(key=lambda x: x["classes_taught"], reverse=True)
        return results

    @staticmethod
    async def get_conversion_funnel(
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        转化漏斗分析
        潜客 → 试课 → 购卡 → 复购 → 推荐的转化率
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # ========== 潜客数 ==========
        leads_raw = await db.execute(
            select(func.count(Lead.id)).where(
                Lead.organization_id == organization_id,
                Lead.created_at >= start_dt,
                Lead.created_at <= end_dt,
            )
        )
        leads = leads_raw.scalar() or 0

        # ========== 试课数（已转化的潜客中有预约记录的） ==========
        # 简化：使用 qualified 状态的潜客作为试课代理
        trials_raw = await db.execute(
            select(func.count(Lead.id)).where(
                Lead.organization_id == organization_id,
                Lead.status == LeadStatus.QUALIFIED,
                Lead.created_at >= start_dt,
                Lead.created_at <= end_dt,
            )
        )
        trials = trials_raw.scalar() or 0

        # ========== 购卡转化数（已转化的潜客） ==========
        conversions_raw = await db.execute(
            select(func.count(Lead.id)).where(
                Lead.organization_id == organization_id,
                Lead.status == LeadStatus.CONVERTED,
                Lead.created_at >= start_dt,
                Lead.created_at <= end_dt,
            )
        )
        conversions = conversions_raw.scalar() or 0

        # ========== 复购数（期间内有2笔以上已支付订单的会员） ==========
        repeat_buyers_raw = await db.execute(
            select(func.count(func.distinct(Order.member_id)))
            .where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= start_dt,
                Order.paid_at <= end_dt,
            )
            .group_by(Order.member_id)
            .having(func.count(Order.id) >= 2)
        )
        renewals = len(list(repeat_buyers_raw))

        # ========== 推荐数（来源为 referral 的潜客） ==========
        from backend.models.lead import LeadSource
        referrals_raw = await db.execute(
            select(func.count(Lead.id)).where(
                Lead.organization_id == organization_id,
                Lead.source == LeadSource.REFERRAL,
                Lead.created_at >= start_dt,
                Lead.created_at <= end_dt,
            )
        )
        referrals = referrals_raw.scalar() or 0

        # ========== 转化率 ==========
        lead_to_trial_rate = round((trials / leads * 100), 1) if leads > 0 else 0.0
        trial_to_conversion_rate = round((conversions / trials * 100), 1) if trials > 0 else 0.0
        conversion_to_renewal_rate = round((renewals / conversions * 100), 1) if conversions > 0 else 0.0

        return {
            "leads": leads,
            "trials": trials,
            "conversions": conversions,
            "renewals": renewals,
            "referrals": referrals,
            "lead_to_trial_rate": lead_to_trial_rate,
            "trial_to_conversion_rate": trial_to_conversion_rate,
            "conversion_to_renewal_rate": conversion_to_renewal_rate,
        }

    @staticmethod
    async def get_store_comparison_analytics(
        db: AsyncSession,
        organization_id: int,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """
        门店对比分析（深度版）
        - 各门店综合评分
        - 各维度排名
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # 获取所有门店
        stores_result = await db.execute(
            select(Store.id, Store.name).where(
                Store.organization_id == organization_id,
                Store.is_active.is_(True),
            )
        )
        stores = [(r.id, r.name) for r in stores_result]

        if not stores:
            return []

        store_ids = [s[0] for s in stores]

        # Batch: revenue per store
        revenue_rows = await db.execute(
            select(
                Order.store_id,
                func.coalesce(func.sum(Order.actual_amount), 0).label("revenue"),
            )
            .where(
                Order.organization_id == organization_id,
                Order.store_id.in_(store_ids),
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= start_dt,
                Order.paid_at <= end_dt,
            )
            .group_by(Order.store_id)
        )
        revenue_map = {r.store_id: float(r.revenue) for r in revenue_rows}

        # Batch: total members per store
        members_rows = await db.execute(
            select(
                Member.store_id,
                func.count(Member.id).label("count"),
            )
            .where(
                Member.organization_id == organization_id,
                Member.store_id.in_(store_ids),
            )
            .group_by(Member.store_id)
        )
        members_map = {r.store_id: r.count for r in members_rows}

        # Batch: new members per store
        new_members_rows = await db.execute(
            select(
                Member.store_id,
                func.count(Member.id).label("count"),
            )
            .where(
                Member.organization_id == organization_id,
                Member.store_id.in_(store_ids),
                Member.created_at >= start_dt,
                Member.created_at <= end_dt,
            )
            .group_by(Member.store_id)
        )
        new_members_map = {r.store_id: r.count for r in new_members_rows}

        # Batch: bookings per store
        bookings_rows = await db.execute(
            select(
                CourseSchedule.store_id,
                func.count(Booking.id).label("count"),
            )
            .join(Booking, Booking.schedule_id == CourseSchedule.id)
            .where(
                Booking.organization_id == organization_id,
                CourseSchedule.store_id.in_(store_ids),
                Booking.status != BookingStatus.CANCELLED,
                CourseSchedule.start_time >= start_dt,
                CourseSchedule.start_time <= end_dt,
            )
            .group_by(CourseSchedule.store_id)
        )
        bookings_map = {r.store_id: r.count for r in bookings_rows}

        # Batch: avg fill rate per store
        fill_rows = await db.execute(
            select(
                CourseSchedule.store_id,
                func.avg(
                    func.cast(CourseSchedule.enrolled_count, SAFloat)
                    / func.nullif(Course.max_attendees, 0)
                ).label("avg_fill"),
            )
            .join(Course, CourseSchedule.course_id == Course.id)
            .where(
                CourseSchedule.organization_id == organization_id,
                CourseSchedule.store_id.in_(store_ids),
                CourseSchedule.start_time >= start_dt,
                CourseSchedule.start_time <= end_dt,
                CourseSchedule.status != "cancelled",
            )
            .group_by(CourseSchedule.store_id)
        )
        fill_map = {r.store_id: round(float(r.avg_fill or 0) * 100, 1) for r in fill_rows}

        results = []
        for store_id, store_name in stores:
            total_revenue = revenue_map.get(store_id, 0.0)
            total_members = members_map.get(store_id, 0)
            new_members = new_members_map.get(store_id, 0)
            total_bookings = bookings_map.get(store_id, 0)
            avg_fill_rate = fill_map.get(store_id, 0.0)

            score = round(
                min(total_revenue / 10000, 30)
                + min(total_members / 100, 20)
                + min(avg_fill_rate / 100 * 25, 25)
                + min(new_members / 50, 25),
                1
            )

            results.append({
                "store_id": store_id,
                "store_name": store_name,
                "total_revenue": total_revenue,
                "total_members": total_members,
                "total_bookings": total_bookings,
                "avg_fill_rate": avg_fill_rate,
                "new_members": new_members,
                "score": score,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
