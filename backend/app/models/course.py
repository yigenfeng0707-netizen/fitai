from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, date, time

class CourseCategory(Base):
    __tablename__ = "course_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    color = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    courses = relationship("Course", back_populates="category")

class Classroom(Base):
    __tablename__ = "classrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    name = Column(String(50), nullable=False)
    capacity = Column(Integer, default=20)
    equipment = Column(JSON)
    status = Column(String(20), default="available")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    schedules = relationship("Schedule", back_populates="classroom")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey("course_categories.id"))
    course_type = Column(String(20), nullable=False)
    duration = Column(Integer, nullable=False)
    price = Column(DECIMAL(10,2), nullable=False)
    description = Column(String(500))
    max_capacity = Column(Integer, default=20)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("CourseCategory", back_populates="courses")
    schedules = relationship("Schedule", back_populates="course")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    classroom_id = Column(Integer, ForeignKey("classrooms.id"))
    coach_id = Column(Integer, ForeignKey("coaches.id"))
    date = Column(date, nullable=False)
    start_time = Column(time, nullable=False)
    end_time = Column(time, nullable=False)
    status = Column(String(20), default="scheduled")
    max_capacity = Column(Integer)
    current_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    course = relationship("Course", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")
    coach = relationship("Coach", back_populates="schedules")