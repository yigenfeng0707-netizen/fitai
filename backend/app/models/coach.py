from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, date, time

class Coach(Base):
    __tablename__ = "coaches"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    coach_no = Column(String(50), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True)
    email = Column(String(100))
    avatar = Column(String(255))
    qualifications = Column(JSON)
    specialties = Column(JSON)
    hourly_rate = Column(DECIMAL(8,2))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    schedules = relationship("Schedule", back_populates="coach")
    teaching_records = relationship("TeachingRecord", back_populates="coach")

class CoachSchedule(Base):
    __tablename__ = "coach_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"))
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(time, nullable=False)
    end_time = Column(time, nullable=False)
    status = Column(String(20), default="available")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    coach = relationship("Coach")

class TeachingRecord(Base):
    __tablename__ = "teaching_records"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    date = Column(date, nullable=False)
    duration = Column(Integer)
    attendees = Column(Integer)
    rating = Column(Integer)
    notes = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    coach = relationship("Coach", back_populates="teaching_records")
    schedule = relationship("Schedule")