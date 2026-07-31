"""
Agent Orchestrator - ReAct (Reasoning + Acting) loop core.

Implements the four Agentic capabilities required by OPC:
1. Autonomous planning - LLM decomposes user intent into multi-step plans
2. Tool calling - Executes registered tools via function calling
3. Long-term memory - Retrieves and stores member context
4. Reflection - Checks result completeness and re-plans if needed
"""
import json
import logging
from typing import Optional
from datetime import datetime, timezone

from backend.config import settings
from backend.agent.llm.qwen_client import QwenClient
from backend.agent.tools.registry import ToolRegistry
from backend.agent.memory.member_memory import MemberMemoryStore
from backend.agent.personas import AgentRole, resolve_persona, get_persona_prompt, get_persona_tools

logger = logging.getLogger(__name__)

# Tools that only read data (safe for all roles)
READ_ONLY_TOOLS = {
    "get_member_profile", "get_body_tests", "get_member_consumption",
    "get_member_bookings", "get_member_attendance_rate",
    "search_courses", "get_course_schedule", "check_schedule_conflict",
    "get_coach_profile", "list_coaches", "get_coach_schedule", "get_coach_stats",
    "get_dashboard_insights", "get_revenue_stats", "get_member_retention",
    "get_dormant_members",
}

# Tools that write/modify data (restricted by role)
WRITE_TOOLS = {
    "book_course", "cancel_booking",
}

# Persona name aliases for backward compat
PERSONA_ALIASES = {
    "health": AgentRole.HEALTH_CONSULTANT,
    "ops": AgentRole.STUDIO_OPS,
    "growth": AgentRole.GROWTH_ENGINE,
}


class AgentOrchestrator:
    """Core ReAct loop: LLM reasoning -> tool execution -> result feedback -> re-reasoning."""

    def __init__(self, llm: QwenClient, tools: ToolRegistry, memory: MemberMemoryStore):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.max_iterations = settings.AGENT_MAX_ITERATIONS
        self.reflection_enabled = settings.AGENT_REFLECTION_ENABLED

    async def run(
        self,
        user_input: str,
        user_role: str,
        organization_id: int,
        db,
        member_id: Optional[int] = None,
        persona: Optional[str] = None,
    ) -> dict:
        """
        Execute the Agent loop for a user request.

        Args:
            user_input: Natural language request from user
            user_role: RBAC role (super_admin/owner/coach/front_desk/finance)
            organization_id: Tenant isolation boundary
            db: Database session
            member_id: Optional context member ID
            persona: Optional persona override ("health_consultant" / "studio_ops" / "growth_engine")

        Returns:
            dict with: answer, tool_calls, iterations, persona
        """
        # 1. Resolve persona and build system prompt
        resolved_persona = resolve_persona(user_role, persona)
        system_prompt = get_persona_prompt(resolved_persona, organization_id, user_role)

        # 2. Retrieve long-term memory
        memory_context = ""
        if member_id:
            try:
                memory_context = await self.memory.retrieve(member_id, organization_id, db)
            except Exception:
                logger.warning("Memory retrieval failed, continuing without", exc_info=True)

        # 3. Initialize messages
        messages = [{"role": "system", "content": system_prompt}]
        if memory_context:
            messages.append({
                "role": "system",
                "content": f"Member context (long-term memory):\n{memory_context}",
            })
        messages.append({"role": "user", "content": user_input})

        # 4. Determine allowed tools by persona (intersected with role permissions)
        allowed_tools = self._get_allowed_tools(user_role, resolved_persona)
        openai_tools = self.tools.get_openai_tools(allowed_tools) if allowed_tools else None

        # 5. ReAct loop
        tool_calls_log = []
        for iteration in range(self.max_iterations):
            try:
                response = await self.llm.chat(
                    messages=messages,
                    tools=openai_tools,
                )
            except Exception as e:
                logger.exception("LLM call failed at iteration %d", iteration)
                return {
                    "answer": f"AI service temporarily unavailable: {str(e)}",
                    "tool_calls": tool_calls_log,
                    "iterations": iteration + 1,
                }

            choice = response.choices[0]
            message = choice.message

            # No tool calls -> Agent is done reasoning
            if not message.tool_calls:
                result = message.content or ""

                # Reflection check: if we used tools but result is very short, ask for more detail
                if (self.reflection_enabled and len(tool_calls_log) > 0
                        and len(result) < 80 and iteration < self.max_iterations - 1):
                    messages.append({"role": "assistant", "content": result})
                    messages.append({
                        "role": "user",
                        "content": "Your previous response was brief. Please provide a more detailed analysis based on the tool results you obtained.",
                    })
                    continue

                # Store interaction to memory
                if member_id:
                    try:
                        await self.memory.store(
                            member_id, organization_id, db,
                            user_input, result, tool_calls_log,
                        )
                    except Exception:
                        logger.warning("Memory storage failed", exc_info=True)

                return {
                    "answer": result,
                    "tool_calls": tool_calls_log,
                    "iterations": iteration + 1,
                    "persona": resolved_persona.value,
                }

            # Has tool calls -> execute them
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ] if message.tool_calls else None,
            })

            for tc in message.tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}

                # Inject organization_id and member_id context
                args["organization_id"] = organization_id
                if member_id and "member_id" not in args:
                    args["member_id"] = member_id

                # Permission check
                if tool_name not in allowed_tools:
                    tool_result = {"error": f"Permission denied: role '{user_role}' cannot use tool '{tool_name}'"}
                else:
                    logger.info("Executing tool: %s args=%s", tool_name, {k: v for k, v in args.items() if k != "organization_id"})
                    tool_result = await self.tools.execute(tool_name, db, **args)

                tool_calls_log.append({
                    "tool": tool_name,
                    "args": {k: v for k, v in args.items() if k != "organization_id"},
                    "result": tool_result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })

        # Max iterations reached
        return {
            "answer": "I've reached the maximum number of reasoning steps. Please try narrowing down your question or break it into smaller parts.",
            "tool_calls": tool_calls_log,
            "iterations": self.max_iterations,
            "persona": resolved_persona.value,
        }

    def _build_system_prompt(self, role: str, org_id: int) -> str:
        """Build role-aware system prompt."""
        role_desc = {
            "super_admin": "full system access",
            "owner": "store owner/manager with read + marketing access",
            "coach": "coach with read-only access to own data",
            "front_desk": "front desk staff with member + booking access",
            "finance": "finance staff with revenue data access",
        }.get(role, f"role: {role}")

        return f"""You are FitAI Agent, an intelligent assistant for a fitness/yoga/training studio management system.

You are serving organization #{org_id}. The current user role is '{role}' ({role_desc}).

You can help with:
1. Member management - query profiles, body tests, consumption, attendance
2. Course management - search courses, check schedules, book/cancel
3. Coach management - query coach profiles, schedules, stats
4. Business analytics - revenue, retention, dormant members, dashboard insights
5. Operations - schedule conflict detection, dormant member identification

Guidelines:
- Only operate on data within organization #{org_id}
- Respect role permissions: {role} has limited tool access
- For booking/cancellation, confirm with user before executing
- Use a professional yet friendly tone, like a senior fitness consultant
- When presenting data, add brief analysis and actionable suggestions
- If a tool returns an error, explain it to the user and suggest alternatives
- Respond in Chinese unless the user speaks English

Remember: you are an Agent that thinks step-by-step and takes actions through tools. Always plan what tools to call first, then synthesize the results into a helpful response.
"""

    def _get_allowed_tools(self, role: str, persona: AgentRole = None) -> set[str]:
        """Get allowed tool names based on RBAC role and persona."""
        # Start with persona-specific tools
        if persona:
            persona_tools = get_persona_tools(persona)
        else:
            persona_tools = self.tools.tool_names

        # Intersect with role-based permissions
        if role in ("super_admin", "owner"):
            # Owner/admin can use all persona tools including write ops
            return persona_tools
        if role == "front_desk":
            # Front desk: read-only + booking ops within persona
            return persona_tools & (READ_ONLY_TOOLS | {"book_course", "cancel_booking"})
        if role in ("coach", "finance"):
            # Coach/finance: read-only within persona
            return persona_tools & READ_ONLY_TOOLS
        # Default: read-only within persona
        return persona_tools & READ_ONLY_TOOLS
