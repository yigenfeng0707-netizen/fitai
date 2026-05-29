"""
数据库模型 - 课程
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin, StoreScopeMixin


class CourseType(str, Enum):
    """课程类型"""
    GROUP = "group"             # 团课
    PRIVATE = "private"         # 私教课
    SEMI_PRIVATE = "semi_private"  # 半私教


class Course(Base, TenantMixin):
    """课程表"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 类型
    course_type = Column(SQLEnum(CourseType), nullable=False)

    # 时长
    duration_minutes = Column(Integer, default=60)  # 课程时长(分钟)

    # 教室
    room = Column(String(50), nullable=True)  # 教室

    # 价格
    price = Column(Float, nullable=True)  # 单次价格
    package_price = Column(Float, nullable=True)  # 套餐价格

    # 教练
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=True, index=True)
    coach = relationship("Coach", back_populates="courses")

    # 状态
    is_active = Column(Boolean, default=True, index=True)

    # 限购
    max_attendees = Column(Integer, default=10)  # 团课最大人数

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CourseSchedule(Base, TenantMixin, StoreScopeMixin):
    """课程排期表"""
    __tablename__ = "course_schedules"

    __table_args__ = (
        Index("ix_cschedules_org_start", "organization_id", "start_time"),
        Index("ix_cschedules_org_course_start", "organization_id", "course_id", "start_time"),
        Index("ix_cschedules_course_id", "course_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    course = relationship("Course", back_populates="schedules")

    # 时间
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)

    # 状态
    status = Column(String(20), default="scheduled")  # scheduled, cancelled, completed

    # 已报名人数
    enrolled_count = Column(Integer, default=0)

    # 备注
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

Course.schedules = relationship("CourseSchedule", back_populates="course")
