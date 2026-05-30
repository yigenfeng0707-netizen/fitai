"""
健身预约 booking model
"""
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Index
from backend.database_base import Base, TenantMixin, StoreScopeMixin
from sqlalchemy.orm import relationship


class BookingStatus(str, Enum):
    """预约状态"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class Booking(Base, TenantMixin, StoreScopeMixin):
    """预约表"""
    __tablename__ = "bookings"

    __table_args__ = (
        Index("ix_bookings_org_status_created", "organization_id", "status", "created_at"),
        Index("ix_bookings_org_member_created", "organization_id", "member_id", "created_at"),
        Index("ix_bookings_member_status", "member_id", "status"),
        Index("ix_bookings_schedule_id", "schedule_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    member = relationship("Member", back_populates="bookings")

    schedule_id = Column(Integer, ForeignKey("course_schedules.id"), nullable=False)
    schedule = relationship("CourseSchedule", back_populates="bookings")

    status = Column(SAEnum(BookingStatus), default=BookingStatus.PENDING)

    check_in_time = Column(DateTime, nullable=True)
    check_in_method = Column(String(20), nullable=True)

    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancel_reason = Column(String(200), nullable=True)

    notes = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


# 反向关系 (imported here to break circular dependency)
from backend.models.course import CourseSchedule  # noqa: E402
CourseSchedule.bookings = relationship("Booking", back_populates="schedule")
