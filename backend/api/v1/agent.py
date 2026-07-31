"""
API - Agent chat endpoint.

Natural language entry point for the FitAI Agent.
Supports three personas: health_consultant, studio_ops, growth_engine.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.config import settings

router = APIRouter()


class AgentRequest(BaseModel):
    message: str
    member_id: int | None = None
    persona: str | None = None  # "health_consultant" / "studio_ops" / "growth_engine"
    context: dict | None = None


class AgentResponse(BaseModel):
    answer: str
    tool_calls: list[dict]
    iterations: int
    persona: str


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(
    req: AgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agent chat endpoint - natural language interaction with persona support."""
    if not settings.DASHSCOPE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Agent service not configured. Set DASHSCOPE_API_KEY in .env",
        )

    from backend.agent.bootstrap import get_orchestrator

    orch = get_orchestrator(db)
    result = await orch.run(
        user_input=req.message,
        user_role=current_user.role if hasattr(current_user, "role") else "front_desk",
        organization_id=current_user.organization_id,
        db=db,
        member_id=req.member_id,
        persona=req.persona,
    )
    return AgentResponse(**result)


@router.get("/tools")
async def list_tools(
    current_user: User = Depends(get_current_user),
):
    """List all available Agent tools."""
    from backend.agent.bootstrap import get_tool_registry
    tools = get_tool_registry()
    return {"tools": tools.list_tools(), "total": len(tools.list_tools())}


@router.get("/health")
async def agent_health():
    """Check if Agent service is configured and ready."""
    return {
        "configured": bool(settings.DASHSCOPE_API_KEY),
        "model": settings.QWEN_MODEL,
        "base_url": settings.LLM_BASE_URL,
        "max_iterations": settings.AGENT_MAX_ITERATIONS,
        "reflection_enabled": settings.AGENT_REFLECTION_ENABLED,
        "personas": ["health_consultant", "studio_ops", "growth_engine"],
        "fallback_enabled": settings.LLM_FALLBACK_ENABLED and bool(settings.LLM_FALLBACK_API_KEY),
        "fallback_model": settings.LLM_FALLBACK_MODEL or None,
    }


@router.get("/personas")
async def list_personas(
    current_user: User = Depends(get_current_user),
):
    """List available Agent personas with descriptions."""
    from backend.agent.personas import AgentRole, PERSONA_TOOLS
    return {
        "personas": [
            {
                "id": AgentRole.HEALTH_CONSULTANT.value,
                "name": "Health Consultant",
                "name_cn": "Health Consultant",
                "description": "Member-facing health advisor - body analysis, course recommendations, attendance tracking",
                "tools": list(PERSONA_TOOLS[AgentRole.HEALTH_CONSULTANT]),
            },
            {
                "id": AgentRole.STUDIO_OPS.value,
                "name": "Studio Ops Assistant",
                "name_cn": "Studio Ops Assistant",
                "description": "Owner-facing operations brain - revenue analysis, coach performance, schedule optimization",
                "tools": list(PERSONA_TOOLS[AgentRole.STUDIO_OPS]),
            },
            {
                "id": AgentRole.GROWTH_ENGINE.value,
                "name": "Growth Engine",
                "name_cn": "Growth Engine",
                "description": "Marketing-facing growth strategist - dormant reactivation, upsell, retention analysis",
                "tools": list(PERSONA_TOOLS[AgentRole.GROWTH_ENGINE]),
            },
        ]
    }


@router.post("/chat/stream")
async def agent_chat_stream(
    req: AgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agent chat with SSE streaming. Returns server-sent events for real-time tool calls and response."""
    if not settings.DASHSCOPE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Agent service not configured. Set DASHSCOPE_API_KEY in .env",
        )

    from backend.agent.bootstrap import get_orchestrator

    orch = get_orchestrator(db)

    async def event_generator():
        async for event in orch.run_stream(
            user_input=req.message,
            user_role=current_user.role if hasattr(current_user, "role") else "front_desk",
            organization_id=current_user.organization_id,
            db=db,
            member_id=req.member_id,
            persona=req.persona,
        ):
            yield f"data: {event}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
