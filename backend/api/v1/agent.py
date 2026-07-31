"""
API - Agent chat endpoint.

Natural language entry point for the FitAI Agent.
"""
from fastapi import APIRouter, Depends, HTTPException
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
    context: dict | None = None


class AgentResponse(BaseModel):
    answer: str
    tool_calls: list[dict]
    iterations: int


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(
    req: AgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agent chat endpoint - natural language interaction."""
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
        "max_iterations": settings.AGENT_MAX_ITERATIONS,
        "reflection_enabled": settings.AGENT_REFLECTION_ENABLED,
    }
