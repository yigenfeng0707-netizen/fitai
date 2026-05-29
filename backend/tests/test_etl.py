"""ETL / 数据仓库测试"""
import pytest
from datetime import datetime, timedelta, date

from sqlalchemy import select

from backend.models.member import Member, MemberStatus, CardType
from backend.models.coach import Coach
from backend.models.course import Course, CourseType, CourseSchedule
from backend.models.booking import Booking, BookingStatus
from backend.models.order import Order, OrderStatus
from backend.models.daily_stats import DailyStats
from backend.models.member_lifecycle import MemberLifecycleEvent
from backend.models.coach_stats import CoachDailyStats
from backend.services.etl_service import ETLService


class TestGenerateDailyStats:
    """每日统计生成测试"""

    @pytest.mark.asyncio
    async def test_generate_daily_stats(self, db):
        """无数据时生成空统计"""
        org_id = 1
        stat_date = date(2026, 5, 28)

        result = await ETLService.generate_daily_stats(db, org_id, stat_date)

        assert result["stat_date"] == "2026-05-28"
        assert result["store_id"] is None
        assert result["total_revenue"] == 0
        assert result["order_count"] == 0
        assert result["total_members"] == 0
        assert result["new_members"] == 0
        assert result["total_bookings"] == 0
        assert result["checked_in"] == 0
        assert result["total_classes"] == 0

        # 验证数据已写入
        stats = await db.execute(
            select(DailyStats).where(
                DailyStats.organization_id == org_id,
                DailyStats.stat_date == stat_date,
            )
        )
        row = stats.scalar_one_or_none()
        assert row is not None
        assert row.total_revenue == 0

    @pytest.mark.asyncio
    async def test_generate_daily_stats_with_store(self, db):
        """指定门店生成统计"""
        org_id = 1
        stat_date = date(2026, 5, 28)
        store_id = 99

        result = await ETLService.generate_daily_stats(
            db, org_id, stat_date, store_id=store_id
        )

        assert result["store_id"] == 99

        # 验证数据已写入
        stats = await db.execute(
            select(DailyStats).where(
                DailyStats.organization_id == org_id,
                DailyStats.stat_date == stat_date,
                DailyStats.store_id == store_id,
            )
        )
        row = stats.scalar_one_or_none()
        assert row is not None

    @pytest.mark.asyncio
    async def test_generate_daily_stats_with_data(self, db):
        """有数据时正确聚合统计"""
        org_id = 1
        now = datetime.utcnow()
        stat_date = now.date()

        # 创建教练
        coach = Coach(
            name="测试教练", phone="13800009999",
            is_active=True, organization_id=org_id,
        )
        db.add(coach)
        await db.flush()

        # 创建课程
        course = Course(
            name="测试团课", course_type=CourseType.GROUP,
            duration_minutes=60, price=100, max_attendees=10,
            is_active=True, coach_id=coach.id, organization_id=org_id,
        )
        db.add(course)
        await db.flush()

        # 创建排期
        schedule = CourseSchedule(
            course_id=course.id,
            start_time=now.replace(hour=10, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=11, minute=0, second=0, microsecond=0),
            status="completed", enrolled_count=5,
            organization_id=org_id,
        )
        db.add(schedule)
        await db.flush()

        # 创建会员
        member = Member(
            name="测试会员", phone="13900008888",
            card_type=CardType.YEARLY, status=MemberStatus.ACTIVE,
            total_consumption=5000, organization_id=org_id,
        )
        db.add(member)
        await db.flush()

        # 创建已支付订单
        order = Order(
            order_no="ETL20260528001",
            member_id=member.id,
            amount=1000, discount=0, actual_amount=1000,
            payment_method="wechat", payment_status=OrderStatus.PAID,
            product_type="card", subject="年卡",
            paid_at=now, created_at=now,
            organization_id=org_id,
        )
        db.add(order)
        await db.flush()

        # 创建预约
        booking = Booking(
            member_id=member.id,
            schedule_id=schedule.id,
            status=BookingStatus.CHECKED_IN,
            check_in_time=now,
            organization_id=org_id,
        )
        db.add(booking)
        await db.flush()

        # 生成统计
        result = await ETLService.generate_daily_stats(db, org_id, stat_date)

        assert result["total_revenue"] == 1000
        assert result["order_count"] == 1
        assert result["total_members"] == 1
        assert result["active_members"] == 1
        assert result["total_bookings"] == 1
        assert result["checked_in"] == 1
        assert result["total_classes"] == 1

    @pytest.mark.asyncio
    async def test_generate_daily_stats_upsert(self, db):
        """重复生成时更新而非重复插入"""
        org_id = 1
        stat_date = date(2026, 5, 28)

        # 第一次生成
        await ETLService.generate_daily_stats(db, org_id, stat_date)

        # 第二次生成
        await ETLService.generate_daily_stats(db, org_id, stat_date)

        # 验证只有一条记录
        stats = await db.execute(
            select(DailyStats).where(
                DailyStats.organization_id == org_id,
                DailyStats.stat_date == stat_date,
            )
        )
        rows = stats.scalars().all()
        assert len(rows) == 1


class TestGetDailyStatsRange:
    """查询每日统计范围测试"""

    @pytest.mark.asyncio
    async def test_get_daily_stats_range(self, db):
        """查询日期范围内的统计数据"""
        org_id = 1

        # 生成两天的统计
        await ETLService.generate_daily_stats(db, org_id, date(2026, 5, 27))
        await ETLService.generate_daily_stats(db, org_id, date(2026, 5, 28))

        # 查询
        stats = await db.execute(
            select(DailyStats)
            .where(
                DailyStats.organization_id == org_id,
                DailyStats.stat_date >= date(2026, 5, 27),
                DailyStats.stat_date <= date(2026, 5, 28),
            )
            .order_by(DailyStats.stat_date)
        )
        rows = stats.scalars().all()
        assert len(rows) == 2


class TestMemberLifecycleEvent:
    """会员生命周期事件测试"""

    @pytest.mark.asyncio
    async def test_member_lifecycle_event(self, db):
        """检测新注册会员事件"""
        org_id = 1
        now = datetime.utcnow()
        event_date = now.date()

        # 创建新会员
        member = Member(
            name="新会员", phone="13900007777",
            status=MemberStatus.ACTIVE,
            organization_id=org_id,
        )
        db.add(member)
        await db.flush()

        # 生成生命周期事件
        result = await ETLService.generate_member_lifecycle_events(
            db, org_id, event_date
        )

        assert result["events_created"] >= 1

        # 验证事件已写入
        events = await db.execute(
            select(MemberLifecycleEvent).where(
                MemberLifecycleEvent.organization_id == org_id,
                MemberLifecycleEvent.member_id == member.id,
                MemberLifecycleEvent.event_type == "register",
            )
        )
        event = events.scalar_one_or_none()
        assert event is not None
        assert event.event_date == event_date

    @pytest.mark.asyncio
    async def test_member_lifecycle_first_visit(self, db):
        """检测首次到店事件"""
        org_id = 1
        now = datetime.utcnow()
        event_date = now.date()

        # 创建教练和课程
        coach = Coach(
            name="教练", phone="13800001111",
            is_active=True, organization_id=org_id,
        )
        db.add(coach)
        await db.flush()

        course = Course(
            name="课程", course_type=CourseType.GROUP,
            duration_minutes=60, price=100, max_attendees=10,
            is_active=True, coach_id=coach.id, organization_id=org_id,
        )
        db.add(course)
        await db.flush()

        schedule = CourseSchedule(
            course_id=course.id,
            start_time=now.replace(hour=10, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=11, minute=0, second=0, microsecond=0),
            status="completed", enrolled_count=1,
            organization_id=org_id,
        )
        db.add(schedule)
        await db.flush()

        # 创建会员 (之前没有签到记录)
        member = Member(
            name="首次到店会员", phone="13900006666",
            status=MemberStatus.ACTIVE,
            created_at=now - timedelta(days=5),
            organization_id=org_id,
        )
        db.add(member)
        await db.flush()

        # 创建签到预约
        booking = Booking(
            member_id=member.id,
            schedule_id=schedule.id,
            status=BookingStatus.CHECKED_IN,
            check_in_time=now,
            organization_id=org_id,
        )
        db.add(booking)
        await db.flush()

        # 生成生命周期事件
        result = await ETLService.generate_member_lifecycle_events(
            db, org_id, event_date
        )

        # 验证首次到店事件
        events = await db.execute(
            select(MemberLifecycleEvent).where(
                MemberLifecycleEvent.organization_id == org_id,
                MemberLifecycleEvent.member_id == member.id,
                MemberLifecycleEvent.event_type == "first_visit",
            )
        )
        event = events.scalar_one_or_none()
        assert event is not None


class TestCoachDailyStats:
    """教练每日统计测试"""

    @pytest.mark.asyncio
    async def test_coach_daily_stats(self, db):
        """生成教练每日统计"""
        org_id = 1
        now = datetime.utcnow()
        stat_date = now.date()

        # 创建教练
        coach = Coach(
            name="教练A", phone="13800002222",
            is_active=True, organization_id=org_id,
        )
        db.add(coach)
        await db.flush()

        # 创建课程
        course = Course(
            name="教练A课程", course_type=CourseType.GROUP,
            duration_minutes=60, price=100, max_attendees=10,
            is_active=True, coach_id=coach.id, organization_id=org_id,
        )
        db.add(course)
        await db.flush()

        # 创建排期
        schedule = CourseSchedule(
            course_id=course.id,
            start_time=now.replace(hour=10, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=11, minute=0, second=0, microsecond=0),
            status="completed", enrolled_count=5,
            organization_id=org_id,
        )
        db.add(schedule)
        await db.flush()

        # 生成教练统计
        result = await ETLService.generate_coach_daily_stats(db, org_id, stat_date)

        assert result["stat_date"] == stat_date.isoformat()
        assert result["coaches_processed"] == 1

        # 验证数据已写入
        coach_stats = await db.execute(
            select(CoachDailyStats).where(
                CoachDailyStats.organization_id == org_id,
                CoachDailyStats.coach_id == coach.id,
                CoachDailyStats.stat_date == stat_date,
            )
        )
        row = coach_stats.scalar_one_or_none()
        assert row is not None
        assert row.classes_taught == 1
        assert row.total_students == 5
        assert row.total_hours == 1.0

    @pytest.mark.asyncio
    async def test_coach_daily_stats_upsert(self, db):
        """重复生成教练统计时更新"""
        org_id = 1
        now = datetime.utcnow()
        stat_date = now.date()

        coach = Coach(
            name="教练B", phone="13800003333",
            is_active=True, organization_id=org_id,
        )
        db.add(coach)
        await db.flush()

        course = Course(
            name="教练B课程", course_type=CourseType.GROUP,
            duration_minutes=60, price=100, max_attendees=10,
            is_active=True, coach_id=coach.id, organization_id=org_id,
        )
        db.add(course)
        await db.flush()

        schedule = CourseSchedule(
            course_id=course.id,
            start_time=now.replace(hour=14, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=15, minute=0, second=0, microsecond=0),
            status="completed", enrolled_count=3,
            organization_id=org_id,
        )
        db.add(schedule)
        await db.flush()

        # 生成两次
        await ETLService.generate_coach_daily_stats(db, org_id, stat_date)
        await ETLService.generate_coach_daily_stats(db, org_id, stat_date)

        # 验证只有一条
        coach_stats = await db.execute(
            select(CoachDailyStats).where(
                CoachDailyStats.organization_id == org_id,
                CoachDailyStats.coach_id == coach.id,
                CoachDailyStats.stat_date == stat_date,
            )
        )
        rows = coach_stats.scalars().all()
        assert len(rows) == 1


class TestRetentionCohorts:
    """会员留存分析测试"""

    @pytest.mark.asyncio
    async def test_retention_cohorts(self, db):
        """留存分析 - 无数据时返回空"""
        org_id = 1

        result = await ETLService.get_member_retention_cohorts(db, org_id)

        assert result == []

    @pytest.mark.asyncio
    async def test_retention_cohorts_with_members(self, db):
        """留存分析 - 有会员时返回cohort数据"""
        org_id = 1
        now = datetime.utcnow()

        # 创建不同月份注册的会员
        for i in range(3):
            member = Member(
                name=f"留存会员{i}",
                phone=f"1390000{i:04d}",
                status=MemberStatus.ACTIVE,
                total_consumption=1000 * (i + 1),
                created_at=now - timedelta(days=30 * i),
                organization_id=org_id,
            )
            db.add(member)
        await db.flush()

        result = await ETLService.get_member_retention_cohorts(db, org_id)

        assert len(result) > 0
        # 每个cohort都有基本字段
        for cohort in result:
            assert "cohort_month" in cohort
            assert "cohort_size" in cohort
            assert "retention" in cohort


class TestLifetimeValue:
    """会员生命周期价值测试"""

    @pytest.mark.asyncio
    async def test_lifetime_value(self, db):
        """LTV分析 - 无数据时返回零值"""
        org_id = 1

        result = await ETLService.get_member_lifetime_value(db, org_id)

        assert result["avg_ltv"] == 0
        assert result["total_ltv"] == 0
        assert result["total_members"] == 0
        assert result["by_level"] == []
        assert result["by_card_type"] == []

    @pytest.mark.asyncio
    async def test_lifetime_value_with_data(self, db):
        """LTV分析 - 有数据时正确计算"""
        org_id = 1

        for i in range(5):
            member = Member(
                name=f"LTV会员{i}",
                phone=f"1390001{i:04d}",
                card_type=[CardType.YEARLY, CardType.MONTHLY, CardType.SINGLE, CardType.STORED, CardType.QUARTERLY][i],
                level=(i % 5) + 1,
                status=MemberStatus.ACTIVE,
                total_consumption=1000 * (i + 1),
                organization_id=org_id,
            )
            db.add(member)
        await db.flush()

        result = await ETLService.get_member_lifetime_value(db, org_id)

        assert result["total_members"] == 5
        assert result["avg_ltv"] > 0
        assert result["total_ltv"] > 0
        assert len(result["by_level"]) > 0
        assert len(result["by_card_type"]) > 0


class TestChurnAnalysis:
    """流失分析测试"""

    @pytest.mark.asyncio
    async def test_churn_analysis(self, db):
        """流失分析 - 无数据时返回零值"""
        org_id = 1

        result = await ETLService.get_churn_analysis(db, org_id)

        assert result["total_members"] == 0
        assert result["churned_count"] == 0
        assert result["churn_rate"] == 0
        assert result["at_risk_members"] == []
        assert result["churn_trend"] is not None

    @pytest.mark.asyncio
    async def test_churn_analysis_with_cancelled(self, db):
        """流失分析 - 有注销会员时正确计算"""
        org_id = 1

        # 创建活跃会员
        active_member = Member(
            name="活跃会员", phone="13900020001",
            status=MemberStatus.ACTIVE,
            total_consumption=5000,
            organization_id=org_id,
        )
        db.add(active_member)

        # 创建注销会员
        cancelled_member = Member(
            name="流失会员", phone="13900020002",
            status=MemberStatus.CANCELLED,
            total_consumption=3000,
            organization_id=org_id,
        )
        db.add(cancelled_member)
        await db.flush()

        result = await ETLService.get_churn_analysis(db, org_id)

        assert result["total_members"] == 2
        assert result["churned_count"] == 1
        assert result["churn_rate"] == 50.0


class TestBackfill:
    """历史数据回填测试"""

    @pytest.mark.asyncio
    async def test_backfill(self, db):
        """回填多天统计数据"""
        org_id = 1
        start_date = date(2026, 5, 26)
        end_date = date(2026, 5, 28)

        result = await ETLService.backfill_stats(
            db, org_id, start_date, end_date
        )

        assert result["start_date"] == "2026-05-26"
        assert result["end_date"] == "2026-05-28"
        assert result["total_days"] == 3
        assert result["processed"] == 3
        assert result["errors"] == 0

        # 验证数据已写入
        stats = await db.execute(
            select(DailyStats).where(
                DailyStats.organization_id == org_id,
                DailyStats.stat_date >= start_date,
                DailyStats.stat_date <= end_date,
            )
        )
        rows = stats.scalars().all()
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_backfill_single_day(self, db):
        """回填单天数据"""
        org_id = 1
        stat_date = date(2026, 5, 28)

        result = await ETLService.backfill_stats(
            db, org_id, stat_date, stat_date
        )

        assert result["total_days"] == 1
        assert result["processed"] == 1
