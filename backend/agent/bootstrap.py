"""
Agent bootstrap - initializes and wires all Agent components.

Singleton pattern: LLM client, tool registry, and memory store
are created once and reused across requests.
"""
import logging
from functools import lru_cache

from backend.config import settings
from backend.agent.llm.qwen_client import QwenClient
from backend.agent.tools.registry import ToolRegistry
from backend.agent.tools.member_tools import register_member_tools
from backend.agent.tools.course_tools import register_course_tools
from backend.agent.tools.coach_tools import register_coach_tools
from backend.agent.tools.ops_tools import register_ops_tools
from backend.agent.memory.member_memory import MemberMemoryStore
from backend.agent.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

_llm_client: QwenClient | None = None
_tool_registry: ToolRegistry | None = None
_memory_store: MemberMemoryStore | None = None


def get_llm_client() -> QwenClient:
    """Get or create the LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        if not settings.DASHSCOPE_API_KEY:
            logger.warning(
                "DASHSCOPE_API_KEY not configured, Agent will fail on LLM calls. "
                "Set it in .env or LLM_FALLBACK_* for fallback support."
            )
        _llm_client = QwenClient()
    return _llm_client


def get_tool_registry() -> ToolRegistry:
    """Get or create the tool registry singleton with all tools registered."""
    global _tool_registry
    if _tool_registry is None:
        registry = ToolRegistry()
        register_member_tools(registry)
        register_course_tools(registry)
        register_coach_tools(registry)
        register_ops_tools(registry)
        _tool_registry = registry
        logger.info("Tool registry initialized with %d tools", len(registry.tool_names))
    return _tool_registry


def get_memory_store() -> MemberMemoryStore:
    """Get or create the memory store singleton."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemberMemoryStore()
    return _memory_store


def get_orchestrator(db) -> AgentOrchestrator:
    """Create an orchestrator instance for a request (db is per-request)."""
    return AgentOrchestrator(
        llm=get_llm_client(),
        tools=get_tool_registry(),
        memory=get_memory_store(),
    )
