"""
OPC Demo Scenarios - Three persona showcase scripts.

These scripts demonstrate the three Agent personas in action,
providing ready-to-use demo scenarios for OPC competition submission.

Usage:
    python -m backend.agent.demo_scenarios --list
    python -m backend.agent.demo_scenarios --scenario health
    python -m backend.agent.demo_scenarios --scenario ops
    python -m backend.agent.demo_scenarios --scenario growth
"""
import argparse
import asyncio
import json
import sys
from typing import Optional

# Demo scenarios data - each persona has 3 representative scenarios
DEMO_SCENARIOS = {
    "health_consultant": [
        {
            "id": "health-1",
            "title": "Member body test trend analysis",
            "title_cn": "Member body test trend analysis",
            "input": "Help me check member #42's recent body test results and analyze the trend",
            "expected_tools": ["get_member_profile", "get_body_tests"],
            "description": "Agent retrieves member profile + body test history, compares latest vs previous, highlights improvement/decline",
        },
        {
            "id": "health-2",
            "title": "Course recommendation based on member goals",
            "title_cn": "Course recommendation based on member goals",
            "input": "Member #42 wants to improve flexibility. What courses do you recommend this week?",
            "expected_tools": ["get_member_profile", "search_courses", "get_course_schedule"],
            "description": "Agent fetches member profile, searches relevant courses, checks schedule, recommends with booking option",
        },
        {
            "id": "health-3",
            "title": "Attendance pattern analysis",
            "title_cn": "Attendance pattern analysis",
            "input": "How is member #42's attendance lately? Any concerns?",
            "expected_tools": ["get_member_attendance_rate", "get_member_bookings"],
            "description": "Agent calculates attendance rate, identifies no-show patterns, suggests re-engagement if needed",
        },
    ],
    "studio_ops": [
        {
            "id": "ops-1",
            "title": "Weekly business overview",
            "title_cn": "Weekly business overview",
            "input": "Give me this week's business overview - revenue, attendance, any issues?",
            "expected_tools": ["get_dashboard_insights", "get_revenue_stats"],
            "description": "Agent pulls dashboard insights + revenue stats, synthesizes a weekly business summary with risk alerts",
        },
        {
            "id": "ops-2",
            "title": "Coach performance comparison",
            "title_cn": "Coach performance comparison",
            "input": "Compare our coaches' performance this month. Who's doing well and who needs support?",
            "expected_tools": ["list_coaches", "get_coach_stats"],
            "description": "Agent lists all coaches, fetches stats for each, ranks performance, identifies outliers",
        },
        {
            "id": "ops-3",
            "title": "Dormant member identification",
            "title_cn": "Dormant member identification",
            "input": "Which members haven't visited in the last 30 days? How many are at risk of churning?",
            "expected_tools": ["get_dormant_members", "get_member_retention"],
            "description": "Agent identifies dormant members, cross-references retention data, provides prioritized reactivation list",
        },
    ],
    "growth_engine": [
        {
            "id": "growth-1",
            "title": "Dormant member reactivation campaign",
            "title_cn": "Dormant member reactivation campaign",
            "input": "Design a reactivation campaign for dormant members. Target the top 20 most valuable ones.",
            "expected_tools": ["get_dormant_members", "get_member_consumption"],
            "description": "Agent identifies dormant members, ranks by lifetime value, suggests personalized outreach strategy",
        },
        {
            "id": "growth-2",
            "title": "Membership renewal prediction",
            "title_cn": "Membership renewal prediction",
            "input": "Which members have cards expiring in the next 30 days? Suggest renewal strategies.",
            "expected_tools": ["get_member_profile", "get_member_consumption"],
            "description": "Agent finds members with expiring cards, analyzes their usage patterns, recommends renewal approach",
        },
        {
            "id": "growth-3",
            "title": "High-value member upsell opportunity",
            "title_cn": "High-value member upsell opportunity",
            "input": "Find upsell opportunities - who are our most engaged members and what can we offer them next?",
            "expected_tools": ["get_member_attendance_rate", "get_member_consumption", "get_member_retention"],
            "description": "Agent identifies highly engaged members, analyzes spending patterns, suggests premium upsell offers",
        },
    ],
}


def list_scenarios() -> None:
    """Print all available demo scenarios."""
    print("\n" + "=" * 70)
    print("FitAI Agent - OPC Demo Scenarios")
    print("=" * 70)
    for persona, scenarios in DEMO_SCENARIOS.items():
        print(f"\n[{persona}]")
        for s in scenarios:
            print(f"  {s['id']}: {s['title']}")
            print(f"    Input: \"{s['input']}\"")
            print(f"    Tools: {', '.join(s['expected_tools'])}")
            print(f"    Desc:  {s['description']}")
    print("\n" + "=" * 70)


async def run_scenario(
    scenario_id: str,
    db_url: str,
    dashscope_key: str,
) -> None:
    """Run a single demo scenario against the live Agent."""
    scenario = None
    for persona_scenarios in DEMO_SCENARIOS.values():
        for s in persona_scenarios:
            if s["id"] == scenario_id:
                scenario = s
                break
    if not scenario:
        print(f"Scenario '{scenario_id}' not found. Use --list to see options.")
        return

    print(f"\n{'=' * 70}")
    print(f"Scenario: {scenario['title']}")
    print(f"Input:    \"{scenario['input']}\"")
    print(f"{'=' * 70}\n")

    # This would connect to the real system in production
    print("[Demo mode - connect to live system to see Agent execution]")
    print(f"Expected tools: {scenario['expected_tools']}")
    print(f"Description: {scenario['description']}")


def main():
    parser = argparse.ArgumentParser(description="FitAI Agent OPC Demo Scenarios")
    parser.add_argument("--list", action="store_true", help="List all demo scenarios")
    parser.add_argument("--scenario", type=str, help="Run a specific scenario by ID")
    parser.add_argument("--persona", type=str, choices=["health", "ops", "growth"],
                        help="Run all scenarios for a persona")
    args = parser.parse_args()

    if args.list:
        list_scenarios()
    elif args.scenario:
        asyncio.run(run_scenario(args.scenario, "", ""))
    elif args.persona:
        persona_map = {
            "health": "health_consultant",
            "ops": "studio_ops",
            "growth": "growth_engine",
        }
        persona_key = persona_map[args.persona]
        print(f"\nRunning all {persona_key} scenarios...")
        for s in DEMO_SCENARIOS[persona_key]:
            asyncio.run(run_scenario(s["id"], "", ""))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
