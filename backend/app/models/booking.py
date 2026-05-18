from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    status = Column(String(20), default="pending")
    booked_at = Column(DateTime, default=datetime.utcnow)
    canceled_at = Column(DateTime)
    notes = Column(String(200))
    
    schedule = relationship("Schedule")
    member = relationship("Member")
    attendance = relationship("Attendance", back_populates="booking", uselist=False)

class Attendance(Base):
    __tablename__ = "attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    status = Column(String(20), default="checked_in")
    notes = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    booking = relationship("Booking", back_populates="attendance")