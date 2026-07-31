"""
Agent Tool Registry - tool registration and execution center.

Wraps existing FitAI API endpoints as OpenAI-compatible function tools
that Qwen LLM can call via function calling.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentTool:
    """Represents a single tool the Agent can invoke."""
    name: str
    description: str
    parameters: dict          # JSON Schema for parameters
    handler: Callable         # Async callable: handler(db, **kwargs) -> Any
    category: str = "general"


class ToolRegistry:
    """Registry for all Agent tools. Converts to OpenAI tool format for Qwen."""

    def __init__(self):
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        if tool.name in self._tools:
            logger.warning("Tool %s already registered, overwriting", tool.name)
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s (%s)", tool.name, tool.category)

    def get_openai_tools(self, allowed_names: Optional[set[str]] = None) -> list[dict]:
        """Convert registered tools to OpenAI/Qwen function calling format."""
        result = []
        for name, tool in self._tools.items():
            if allowed_names is not None and name not in allowed_names:
                continue
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            })
        return result

    async def execute(self, name: str, db, **kwargs) -> Any:
        """Execute a tool by name with given arguments."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}
        try:
            result = await tool.handler(db, **kwargs)
            return result
        except Exception as e:
            logger.exception("Tool execution failed: %s", name)
            return {"error": f"Tool execution failed: {str(e)}"}

    def list_tools(self) -> list[dict]:
        """List all registered tools with metadata."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
            }
            for t in self._tools.values()
        ]

    @property
    def tool_names(self) -> set[str]:
        return set(self._tools.keys())
