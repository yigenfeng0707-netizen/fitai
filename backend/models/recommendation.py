from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Index

from backend.database_base import Base, TenantMixin


class AIRecommendation(Base, TenantMixin):
    __tablename__ = "ai_recommendations"

    __table_args__ = (
        Index("ix_airec_org_member_created", "organization_id", "member_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    recommendation_type = Column(String(50), nullable=False, index=True)

    member_id = Column(Integer, ForeignKey("members.id"), nullable=True, index=True)
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(Integer, nullable=True)

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    action_url = Column(String(500), nullable=True)
    meta_data = Column(JSON, nullable=True)

    is_read = Column(Integer, default=0)
    is_applied = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
