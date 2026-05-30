from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin


class BodyTestRecord(Base, TenantMixin):
    __tablename__ = "body_test_records"

    __table_args__ = (
        Index("ix_bodytest_org_member_created", "organization_id", "member_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)

    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    body_fat_percentage = Column(Float, nullable=True)
    muscle_mass = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    bone_mass = Column(Float, nullable=True)
    body_water = Column(Float, nullable=True)
    visceral_fat = Column(Float, nullable=True)
    basal_metabolism = Column(Float, nullable=True)
    body_age = Column(Integer, nullable=True)
    protein = Column(Float, nullable=True)
    score = Column(Float, nullable=True)

    extra_data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    member = relationship("Member", back_populates="body_test_records")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
