"""
数据库模型 - 每日统计汇总
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, JSON, Index
from backend.database_base import Base, TenantMixin


class DailyStats(Base, TenantMixin):
    """每日统计汇总表 - 预聚合数据用于快速查询"""
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, nullable=False, index=True)  # 统计日期
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)  # 门店ID，NULL表示全组织

    # 营收指标
    total_revenue = Column(Float, default=0)  # 总营收
    order_count = Column(Integer, default=0)  # 订单数
    new_members_revenue = Column(Float, default=0)  # 新会员营收
    renewal_revenue = Column(Float, default=0)  # 续费营收
    refund_amount = Column(Float, default=0)  # 退款金额
    avg_order_value = Column(Float, default=0)  # 平均客单价

    # 会员指标
    total_members = Column(Integer, default=0)  # 总会员数
    new_members = Column(Integer, default=0)  # 新增会员
    active_members = Column(Integer, default=0)  # 活跃会员（有预约/消费）
    expired_members = Column(Integer, default=0)  # 过期会员
    frozen_members = Column(Integer, default=0)  # 冻结会员

    # 预约指标
    total_bookings = Column(Integer, default=0)  # 总预约数
    checked_in = Column(Integer, default=0)  # 签到数
    cancelled_bookings = Column(Integer, default=0)  # 取消预约
    no_shows = Column(Integer, default=0)  # 爽约数
    checkin_rate = Column(Float, default=0)  # 签到率

    # 课程指标
    total_classes = Column(Integer, default=0)  # 总课时
    avg_fill_rate = Column(Float, default=0)  # 平均满课率
    popular_course_id = Column(Integer)  # 最热门课程ID
    popular_course_name = Column(String(100))  # 最热门课程名

    # 教练指标
    active_coaches = Column(Integer, default=0)  # 活跃教练数
    total_teaching_hours = Column(Float, default=0)  # 总教学时长

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    __table_args__ = (
        Index('ix_daily_stats_org_date_store', 'organization_id', 'stat_date', 'store_id', unique=True),
        Index('ix_daily_stats_org_date', 'organization_id', 'stat_date'),
    )
