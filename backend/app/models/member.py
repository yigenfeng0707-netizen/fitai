from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class MemberLevel(Base):
    __tablename__ = "member_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    name = Column(String(50), nullable=False)
    min_points = Column(Integer, default=0)
    discount = Column(DECIMAL(4,2), default=1.0)
    privileges = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    members = relationship("Member", back_populates="level")

class MemberCard(Base):
    __tablename__ = "member_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    card_no = Column(String(50), unique=True, nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"))
    card_type = Column(String(20), nullable=False)
    total_hours = Column(DECIMAL(8,2))
    used_hours = Column(DECIMAL(8,2), default=0)
    balance = Column(DECIMAL(10,2), default=0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    member = relationship("Member", back_populates="cards")

class BodyTestRecord(Base):
    __tablename__ = "body_test_records"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    test_date = Column(DateTime, nullable=False)
    height = Column(DECIMAL(5,2))
    weight = Column(DECIMAL(5,2))
    body_fat_rate = Column(DECIMAL(5,2))
    muscle_rate = Column(DECIMAL(5,2))
    bmi = Column(DECIMAL(4,2))
    waist = Column(DECIMAL(5,2))
    hip = Column(DECIMAL(5,2))
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    member = relationship("Member", back_populates="body_tests")

class Member(Base):
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    member_no = Column(String(50), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(100))
    avatar = Column(String(255))
    level_id = Column(Integer, ForeignKey("member_levels.id"))
    points = Column(Integer, default=0)
    tags = Column(JSON)
    status = Column(String(20), default="active")
    freeze_until = Column(DateTime)
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    level = relationship("MemberLevel", back_populates="members")
    cards = relationship("MemberCard", back_populates="member")
    body_tests = relationship("BodyTestRecord", back_populates="member")