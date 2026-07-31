"""
Agent Interaction Log model.

Stores Agent chat history, tool calls, and metadata for:
- Long-term memory: retrieve past interactions for context
- Audit trail: track all Agent actions
- Analytics: measure Agent usage and effectiveness
"""
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class AgentInteractionLog(Base):
    """Agent interaction log for memory and audit."""
    __tablename__ = "agent_interaction_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    member_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    persona: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    agent_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    iterations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    def __repr__(self):
        return f"<AgentInteractionLog(id={self.id}, org={self.organization_id}, persona={self.persona})>"
