"""
AI 服务层 - 封装 AI 推理逻辑
知识点接入 ModelScope，生产环境切换为 Aliyun 模型服务
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from backend.models.member import Member, CardType
from backend.models.course import Course, CourseSchedule
from backend.models.booking import Booking
from backend.models.body_test import BodyTestRecord
from backend.models.order import Order, OrderStatus


class AIService:
    @staticmethod
    async def analyze_body_test(
        db: AsyncSession,
        member_id: int,
        organization_id: int,
    ) -> dict:
        records = await db.execute(
            select(BodyTestRecord)
            .where(
                BodyTestRecord.member_id == member_id,
                BodyTestRecord.organization_id == organization_id,
            )
            .order_by(BodyTestRecord.created_at.desc())
            .limit(2)
        )
        rows = records.scalars().all()

        if not rows:
            return {"current": None, "previous": None, "trends": {}, "suggestions": ["尚无体测数据"]}

        current = rows[0]
        previous = rows[1] if len(rows) > 1 else None

        trends = {}
        suggestions = []

        if previous and current.weight and previous.weight:
            diff = current.weight - previous.weight
            trends["weight_change"] = round(diff, 1)
            if diff > 2:
                suggestions.append(f"体重较上次增加 {diff:.1f}kg，建议增加有氧训练")
            elif diff < -2:
                suggestions.append(f"体重较上次减少 {abs(diff):.1f}kg，注意营养摄入")

        if current.body_fat_percentage is not None:
            bf = current.body_fat_percentage
            if bf > 30:
                suggestions.append(f"体脂率 {bf:.1f}% 偏高，建议加强减脂训练")
            elif bf < 10:
                suggestions.append(f"体脂率 {bf:.1f}% 偏低，注意营养均衡")
            else:
                suggestions.append(f"体脂率 {bf:.1f}% 处于健康范围，继续保持")

            if previous and previous.body_fat_percentage:
                bf_diff = current.body_fat_percentage - previous.body_fat_percentage
                trends["body_fat_change"] = round(bf_diff, 1)
                if bf_diff < -1:
                    suggestions.append(f"体脂率下降 {abs(bf_diff):.1f}%，减脂效果明显")

        if current.bmi is not None:
            bmi = current.bmi
            if bmi < 18.5:
                suggestions.append(f"BMI {bmi:.1f} 偏低，建议增肌增重")
            elif bmi > 24:
                suggestions.append(f"BMI {bmi:.1f} 偏高，建议减脂减重")

        if current.muscle_mass is not None and previous and previous.muscle_mass:
            muscle_diff = current.muscle_mass - previous.muscle_mass
            trends["muscle_mass_change"] = round(muscle_diff, 1)
            if muscle_diff > 0.5:
                suggestions.append(f"肌肉量增加 {muscle_diff:.1f}kg，增肌效果良好")

        if current.score is not None:
            score = current.score
            if score < 60:
                suggestions.append(f"体测得分 {score} 分，建议制定专项改善计划")
            elif score >= 85:
                suggestions.append(f"体测得分 {score} 分，身体素质优秀")

        return {
            "current": current,
            "previous": previous,
            "trends": trends,
            "suggestions": suggestions,
        }

    @staticmethod
    async def recommend_courses(
        db: AsyncSession,
        member_id: int,
        organization_id: int,
    ) -> list[dict]:
        member_result = await db.execute(
            select(Member).where(Member.id == member_id, Member.organization_id == organization_id)
        )
        member = member_result.scalar_one_or_none()
        if not member:
            return []

        recommendations = []

        courses_result = await db.execute(
            select(Course).where(
                Course.organization_id == organization_id,
                Course.is_active.is_(True),
            )
        )
        courses = courses_result.scalars().all()

        bookings_result = await db.execute(
            select(Booking.schedule_id)
            .where(
                Booking.member_id == member_id,
                Booking.organization_id == organization_id,
            )
        )
        schedule_ids = {row[0] for row in bookings_result.all()}
        if schedule_ids:
            schedules_result = await db.execute(
                select(CourseSchedule.course_id).where(CourseSchedule.id.in_(schedule_ids))
            )
            booked_course_ids = {row[0] for row in schedules_result.all()}
        else:
            booked_course_ids = set()

        for course in courses:
            score = 50.0
            reasons = []

            if course.course_type == "private" and member.level >= 3:
                score += 20
                reasons.append("高等级会员适合私教课程")

            if course.course_type == "group":
                score += 10
                reasons.append("团课性价比高，适合常规训练")

            if member.card_type == CardType.SINGLE and course.course_type == "private":
                score += 15
                reasons.append("次卡会员适合预约私教课")

            if member.total_consumption and member.total_consumption > 5000:
                score += 10
                reasons.append("高消费会员推荐进阶课程")

            if course.id in booked_course_ids:
                score -= 20
                reasons.append("已预约过该课程")

            score = min(score, 100)

            recommendations.append({
                "course_id": course.id,
                "course_name": course.name,
                "course_type": course.course_type,
                "price": course.price,
                "duration_minutes": course.duration_minutes,
                "score": round(score, 1),
                "reason": "；".join(reasons) if reasons else "基础推荐",
            })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]

    @staticmethod
    async def get_dashboard_insights(
        db: AsyncSession,
        organization_id: int,
    ) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        today_orders = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= today_start,
            )
        )
        revenue_today = today_orders.scalar() or 0

        month_orders = await db.execute(
            select(func.coalesce(func.sum(Order.actual_amount), 0))
            .where(
                Order.organization_id == organization_id,
                Order.payment_status == OrderStatus.PAID,
                Order.paid_at >= month_start,
            )
        )
        revenue_month = month_orders.scalar() or 0

        active_members_count = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.status == "active",
            )
        )
        active_members = active_members_count.scalar() or 0

        new_members_count = await db.execute(
            select(func.count(Member.id)).where(
                Member.organization_id == organization_id,
                Member.created_at >= month_start,
            )
        )
        new_members_month = new_members_count.scalar() or 0

        bookings_today_count = await db.execute(
            select(func.count(Booking.id)).where(
                Booking.organization_id == organization_id,
                Booking.created_at >= today_start,
            )
        )
        bookings_today = bookings_today_count.scalar() or 0

        today_schedules = await db.execute(
            select(func.count(CourseSchedule.id)).where(
                CourseSchedule.organization_id == organization_id,
                func.date(CourseSchedule.start_time) == func.date(now),
            )
        )
        total_today = today_schedules.scalar() or 0

        completed_today = await db.execute(
            select(func.count(CourseSchedule.id)).where(
                CourseSchedule.organization_id == organization_id,
                func.date(CourseSchedule.start_time) == func.date(now),
                CourseSchedule.status == "completed",
            )
        )
        completed = completed_today.scalar() or 0
        completion_rate = (completed / total_today * 100) if total_today > 0 else 0

        top_courses_result = await db.execute(
            select(
                Course.name,
                func.count(Booking.id).label("booking_count"),
            )
            .join(CourseSchedule, CourseSchedule.course_id == Course.id)
            .join(Booking, Booking.schedule_id == CourseSchedule.id)
            .where(
                Course.organization_id == organization_id,
                Booking.organization_id == organization_id,
            )
            .group_by(Course.name)
            .order_by(func.count(Booking.id).desc())
            .limit(5)
        )
        top_courses = [
            {"name": row[0], "booking_count": row[1]}
            for row in top_courses_result.all()
        ]

        insights = []
        if revenue_month > 0:
            insights.append(f"本月营收 ¥{revenue_month:.0f}")
        if new_members_month > 0:
            insights.append(f"本月新增会员 {new_members_month} 人")
        if completion_rate < 50:
            insights.append(f"今日课程完成率 {completion_rate:.0f}%，建议关注排课执行")
        if active_members > 0 and new_members_month / max(active_members, 1) > 0.2:
            insights.append(f"新会员占比 {(new_members_month/active_members*100):.0f}%，拉新效果显著")

        return {
            "revenue_today": float(revenue_today),
            "revenue_month": float(revenue_month),
            "active_members": active_members,
            "new_members_month": new_members_month,
            "bookings_today": bookings_today,
            "class_completion_rate": round(completion_rate, 1),
            "top_courses": top_courses,
            "insights": insights,
        }


ai_service = AIService()
