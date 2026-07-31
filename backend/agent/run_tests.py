"""
Agent module validation script.

Verifies the Agent layer code structure and importability
without requiring a running database or LLM service.

Usage:
    python -m backend.agent.run_tests
"""
import sys
import importlib
import traceback


def test_imports() -> bool:
    """Test that all Agent modules can be imported."""
    modules = [
        "backend.agent",
        "backend.agent.tools.registry",
        "backend.agent.tools.member_tools",
        "backend.agent.tools.course_tools",
        "backend.agent.tools.coach_tools",
        "backend.agent.tools.ops_tools",
        "backend.agent.llm.qwen_client",
        "backend.agent.memory.member_memory",
        "backend.agent.orchestrator",
        "backend.agent.personas",
        "backend.agent.bootstrap",
        "backend.agent.demo_scenarios",
    ]
    passed = 0
    failed = 0
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"  [PASS] {mod}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {mod}: {e}")
            failed += 1
    print(f"\nImport test: {passed}/{len(modules)} passed, {failed} failed")
    return failed == 0


def test_tool_registry() -> bool:
    """Test tool registration and OpenAI format conversion."""
    try:
        from backend.agent.tools.registry import ToolRegistry, AgentTool
        from backend.agent.tools.member_tools import register_member_tools
        from backend.agent.tools.course_tools import register_course_tools
        from backend.agent.tools.coach_tools import register_coach_tools
        from backend.agent.tools.ops_tools import register_ops_tools

        registry = ToolRegistry()
        register_member_tools(registry)
        register_course_tools(registry)
        register_coach_tools(registry)
        register_ops_tools(registry)

        all_tools = registry.list_tools()
        print(f"  Registered tools: {len(all_tools)}")

        # Verify categories
        categories = {}
        for t in all_tools:
            cat = t["category"]
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in sorted(categories.items()):
            print(f"    {cat}: {count} tools")

        # Check OpenAI format
        openai_tools = registry.get_openai_tools()
        assert len(openai_tools) == len(all_tools), "OpenAI tools count mismatch"
        for t in openai_tools:
            assert "type" in t and t["type"] == "function"
            assert "function" in t
            assert "name" in t["function"]
            assert "parameters" in t["function"]

        # Check filtered tools
        member_only = registry.get_openai_tools({"get_member_profile", "get_body_tests"})
        assert len(member_only) == 2, f"Expected 2, got {len(member_only)}"

        print(f"  [PASS] Tool registry: {len(all_tools)} tools, OpenAI format OK")
        return True
    except Exception as e:
        print(f"  [FAIL] Tool registry: {e}")
        traceback.print_exc()
        return False


def test_personas() -> bool:
    """Test persona resolution and tool sets."""
    try:
        from backend.agent.personas import (
            AgentRole, resolve_persona, get_persona_prompt, get_persona_tools,
        )

        # Test default resolution
        assert resolve_persona("owner") == AgentRole.STUDIO_OPS
        assert resolve_persona("coach") == AgentRole.HEALTH_CONSULTANT
        assert resolve_persona("front_desk") == AgentRole.HEALTH_CONSULTANT
        assert resolve_persona("finance") == AgentRole.STUDIO_OPS

        # Test explicit override
        assert resolve_persona("owner", "growth_engine") == AgentRole.GROWTH_ENGINE
        assert resolve_persona("coach", "health_consultant") == AgentRole.HEALTH_CONSULTANT

        # Test invalid persona falls back to default
        assert resolve_persona("owner", "invalid_persona") == AgentRole.STUDIO_OPS

        # Test prompt generation
        prompt = get_persona_prompt(AgentRole.HEALTH_CONSULTANT, 1, "coach")
        assert "FitAI Health Consultant" in prompt
        assert "Organization ID: 1" in prompt

        # Test tool sets
        health_tools = get_persona_tools(AgentRole.HEALTH_CONSULTANT)
        ops_tools = get_persona_tools(AgentRole.STUDIO_OPS)
        growth_tools = get_persona_tools(AgentRole.GROWTH_ENGINE)

        assert "book_course" in health_tools, "Health consultant should have booking tools"
        assert "get_dormant_members" in ops_tools, "Ops should have dormant members"
        assert "get_revenue_stats" in growth_tools, "Growth should have revenue stats"

        print(f"  [PASS] Personas: {len(AgentRole)} roles, tool sets OK")
        return True
    except Exception as e:
        print(f"  [FAIL] Personas: {e}")
        traceback.print_exc()
        return False


def test_demo_scenarios() -> bool:
    """Test demo scenario data integrity."""
    try:
        from backend.agent.demo_scenarios import DEMO_SCENARIOS

        total = 0
        for persona, scenarios in DEMO_SCENARIOS.items():
            assert len(scenarios) == 3, f"{persona} should have 3 scenarios"
            for s in scenarios:
                assert "id" in s and "title" in s and "input" in s
                assert "expected_tools" in s and len(s["expected_tools"]) > 0
                assert "description" in s
            total += len(scenarios)

        print(f"  [PASS] Demo scenarios: {total} scenarios across {len(DEMO_SCENARIOS)} personas")
        return True
    except Exception as e:
        print(f"  [FAIL] Demo scenarios: {e}")
        traceback.print_exc()
        return False


def test_config() -> bool:
    """Test Agent configuration."""
    try:
        from backend.config import settings

        assert hasattr(settings, "DASHSCOPE_API_KEY"), "Missing DASHSCOPE_API_KEY"
        assert hasattr(settings, "QWEN_MODEL"), "Missing QWEN_MODEL"
        assert hasattr(settings, "AGENT_MAX_ITERATIONS"), "Missing AGENT_MAX_ITERATIONS"
        assert hasattr(settings, "AGENT_REFLECTION_ENABLED"), "Missing AGENT_REFLECTION_ENABLED"

        print(f"  [PASS] Config: model={settings.QWEN_MODEL}, "
              f"max_iter={settings.AGENT_MAX_ITERATIONS}, "
              f"reflection={settings.AGENT_REFLECTION_ENABLED}")
        return True
    except Exception as e:
        print(f"  [FAIL] Config: {e}")
        return False


def main():
    print("=" * 60)
    print("FitAI Agent Module Validation")
    print("=" * 60)
    print()

    tests = [
        ("Config", test_config),
        ("Imports", test_imports),
        ("Tool Registry", test_tool_registry),
        ("Personas", test_personas),
        ("Demo Scenarios", test_demo_scenarios),
    ]

    results = []
    for name, test_fn in tests:
        print(f"[{name}]")
        try:
            result = test_fn()
        except Exception:
            result = False
            traceback.print_exc()
        results.append((name, result))
        print()

    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, r in results:
        status = "PASS" if r else "FAIL"
        print(f"  {name}: {status}")
    print(f"\nTotal: {passed}/{total} passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
