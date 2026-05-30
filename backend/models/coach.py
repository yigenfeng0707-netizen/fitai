"""
数据库模型 - 教练
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin, StoreScopeMixin


class Coach(Base, TenantMixin, StoreScopeMixin):
    """教练表"""
    __tablename__ = "coaches"

    __table_args__ = (
        Index("ix_coaches_phone", "phone"),
        Index("ix_coaches_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), nullable=True)

    # 资质
    certificates = Column(JSON, nullable=True)  # 资质证书
    specialization = Column(String(100), nullable=True)  # 专长
    introduction = Column(Text, nullable=True)  # 个人介绍

    # 排班
    work_schedule = Column(JSON, nullable=True)  # 排班表 {weekday: [start, end]}

    # 统计
    total_hours = Column(Float, default=0.0)  # 总课时
    total_students = Column(Integer, default=0)  # 服务学员数
    avg_rating = Column(Float, default=0.0)  # 平均评分

    # 状态
    is_active = Column(Boolean, default=True, index=True)

    # 时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # 关联
    members = relationship("Member", back_populates="coach")
    courses = relationship("Course", back_populates="coach")
