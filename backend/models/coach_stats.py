"""
数据库模型 - 教练每日统计
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, Date, ForeignKey, Index
from backend.database_base import Base, TenantMixin


class CoachDailyStats(Base, TenantMixin):
    """教练每日统计表"""
    __tablename__ = "coach_daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)
    stat_date = Column(Date, nullable=False, index=True)

    classes_taught = Column(Integer, default=0)  # 授课数
    total_students = Column(Integer, default=0)  # 总学员数
    avg_rating = Column(Float, default=0)  # 平均评分
    total_hours = Column(Float, default=0)  # 总时长
    new_students = Column(Integer, default=0)  # 新学员数
    revenue_contribution = Column(Float, default=0)  # 营收贡献

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_coach_stats_org_coach_date', 'organization_id', 'coach_id', 'stat_date', unique=True),
    )
