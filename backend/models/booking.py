"""
数据库模型 - 预约
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin


class BookingStatus(str, Enum):
    """预约状态"""
    PENDING = "pending"         # 待确认
    CONFIRMED = "confirmed"     # 已确认
    CHECKED_IN = "checked_in"   # 已签到
    CANCELLED = "cancelled"     # 已取消
    NO_SHOW = "no_show"         # 爽约
    COMPLETED = "completed"     # 已完成


class Booking(Base, TenantMixin):
    """预约表"""
    __tablename__ = "bookings"

    __table_args__ = (
        Index("ix_bookings_member_status", "member_id", "status"),
        Index("ix_bookings_schedule_id", "schedule_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # 关联
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    member = relationship("Member", back_populates="bookings")
    
    schedule_id = Column(Integer, ForeignKey("course_schedules.id"), nullable=False)
    schedule = relationship("CourseSchedule", back_populates="bookings")
    
    # 状态
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    
    # 签到
    check_in_time = Column(DateTime, nullable=True)  # 签到时间
    check_in_method = Column(String(20), nullable=True)  # 签到方式: qrcode, manual
    
    # 取消
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancel_reason = Column(String(200), nullable=True)
    
    # 备注
    notes = Column(String(200), nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 反向关系
from backend.models.course import CourseSchedule
CourseSchedule.bookings = relationship("Booking", back_populates="schedule")