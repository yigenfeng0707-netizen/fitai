"""营销规则引擎 API 测试"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_rule(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/marketing/rules", json={
        "name": "新会员欢迎规则",
        "description": "新会员注册时发送欢迎通知",
        "trigger": {
            "event_type": "member_created",
        },
        "conditions": [],
        "actions": [
            {
                "type": "send_notification",
                "params": {
                    "title": "欢迎加入！",
                    "content": "亲爱的{{name}}，欢迎加入我们的健身大家庭！",
                },
            }
        ],
        "is_active": True,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "新会员欢迎规则"
    assert data["trigger_type"] == "member_created"
    assert data["is_active"] is True
    assert len(data["actions"]) == 1


@pytest.mark.asyncio
async def test_list_rules(client: AsyncClient, auth_headers: dict):
    # Create a rule first
    await client.post("/api/v1/marketing/rules", json={
        "name": "列表测试规则",
        "trigger": {"event_type": "member_created"},
        "actions": [{"type": "send_notification", "params": {}}],
    }, headers=auth_headers)

    resp = await client.get("/api/v1/marketing/rules", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_update_rule(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/marketing/rules", json={
        "name": "更新前",
        "trigger": {"event_type": "member_created"},
        "actions": [{"type": "send_notification", "params": {}}],
    }, headers=auth_headers)
    rule_id = create_resp.json()["id"]

    resp = await client.put(f"/api/v1/marketing/rules/{rule_id}", json={
        "name": "更新后",
        "description": "已更新描述",
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "更新后"
    assert data["description"] == "已更新描述"


@pytest.mark.asyncio
async def test_toggle_rule(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/marketing/rules", json={
        "name": "切换测试",
        "trigger": {"event_type": "member_created"},
        "actions": [{"type": "send_notification", "params": {}}],
        "is_active": True,
    }, headers=auth_headers)
    rule_id = create_resp.json()["id"]

    # Toggle off
    resp = await client.post(f"/api/v1/marketing/rules/{rule_id}/toggle", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_active"] is False

    # Toggle on
    resp = await client.post(f"/api/v1/marketing/rules/{rule_id}/toggle", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_delete_rule(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/marketing/rules", json={
        "name": "待删除",
        "trigger": {"event_type": "member_created"},
        "actions": [{"type": "send_notification", "params": {}}],
    }, headers=auth_headers)
    rule_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/marketing/rules/{rule_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.get(f"/api/v1/marketing/rules/{rule_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_process_event_member_created(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    # Create a rule
    await client.post("/api/v1/marketing/rules", json={
        "name": "欢迎通知规则",
        "trigger": {"event_type": "member_created"},
        "conditions": [],
        "actions": [
            {
                "type": "send_notification",
                "params": {"title": "欢迎", "content": "欢迎加入"},
            }
        ],
    }, headers=auth_headers)

    # Create a member
    from backend.models.member import Member
    member = Member(name="测试会员", phone="13900009999", organization_id=1)
    db.add(member)
    await db.commit()

    # Process event
    resp = await client.post("/api/v1/marketing/events", json={
        "event_type": "member_created",
        "entity_id": member.id,
    }, headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["matched"] is True
    assert len(results[0]["actions_executed"]) >= 1


@pytest.mark.asyncio
async def test_process_event_with_conditions(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    # Create a rule with condition
    await client.post("/api/v1/marketing/rules", json={
        "name": "高级会员规则",
        "trigger": {"event_type": "member_created"},
        "conditions": [
            {
                "type": "level",
                "operator": "gte",
                "value": 3,
            }
        ],
        "actions": [
            {
                "type": "send_notification",
                "params": {"title": "VIP欢迎", "content": "尊敬的VIP会员"},
            }
        ],
    }, headers=auth_headers)

    # Create a low-level member
    from backend.models.member import Member
    member = Member(name="普通会员", phone="13900008888", level=1, organization_id=1)
    db.add(member)
    await db.commit()

    # Process event - should not match
    resp = await client.post("/api/v1/marketing/events", json={
        "event_type": "member_created",
        "entity_id": member.id,
    }, headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    # Condition: level >= 3, but member level is 1, so should not match
    assert results[0]["matched"] is False


@pytest.mark.asyncio
async def test_condition_evaluation_tag_match(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    # Rule with tag condition - use "in" operator for list containment
    await client.post("/api/v1/marketing/rules", json={
        "name": "标签匹配规则",
        "trigger": {"event_type": "member_created"},
        "conditions": [
            {
                "type": "tags",
                "operator": "contains",
                "value": ["VIP"],
            }
        ],
        "actions": [
            {"type": "send_notification", "params": {"title": "VIP", "content": "VIP通知"}},
        ],
    }, headers=auth_headers)

    # Member with VIP tag
    from backend.models.member import Member
    member = Member(name="VIP会员", phone="13900007777", tags=["VIP", "高频"], organization_id=1)
    db.add(member)
    await db.commit()

    resp = await client.post("/api/v1/marketing/events", json={
        "event_type": "member_created",
        "entity_id": member.id,
    }, headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["matched"] is True


@pytest.mark.asyncio
async def test_condition_evaluation_level(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    # Rule with level condition
    await client.post("/api/v1/marketing/rules", json={
        "name": "等级条件规则",
        "trigger": {"event_type": "member_created"},
        "conditions": [
            {
                "type": "level",
                "operator": "eq",
                "value": 5,
            }
        ],
        "actions": [
            {"type": "send_notification", "params": {"title": "最高级", "content": "最高级会员"}},
        ],
    }, headers=auth_headers)

    # Member with level 5
    from backend.models.member import Member
    member = Member(name="顶级会员", phone="13900006666", level=5, organization_id=1)
    db.add(member)
    await db.commit()

    resp = await client.post("/api/v1/marketing/events", json={
        "event_type": "member_created",
        "entity_id": member.id,
    }, headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["matched"] is True


@pytest.mark.asyncio
async def test_manual_execute(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    create_resp = await client.post("/api/v1/marketing/rules", json={
        "name": "手动执行规则",
        "trigger": {"event_type": "member_created"},
        "actions": [
            {"type": "send_notification", "params": {"title": "手动", "content": "手动触发"}},
        ],
    }, headers=auth_headers)
    rule_id = create_resp.json()["id"]

    from backend.models.member import Member
    member = Member(name="手动测试", phone="13900005555", organization_id=1)
    db.add(member)
    await db.commit()

    resp = await client.post(f"/api/v1/marketing/rules/{rule_id}/execute", json={
        "event_type": "member_created",
        "entity_id": member.id,
    }, headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_get_trigger_types(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/marketing/trigger-types", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "trigger_types" in data
    assert "member_created" in data["trigger_types"]
    assert "birthday" in data["trigger_types"]


@pytest.mark.asyncio
async def test_get_action_types(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/marketing/action-types", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "action_types" in data
    assert "send_notification" in data["action_types"]
    assert "send_sms" in data["action_types"]


@pytest.mark.asyncio
async def test_rule_logs(client: AsyncClient, db: AsyncSession, auth_headers: dict):
    create_resp = await client.post("/api/v1/marketing/rules", json={
        "name": "日志测试规则",
        "trigger": {"event_type": "member_created"},
        "actions": [{"type": "send_notification", "params": {"title": "日志", "content": "测试"}}],
    }, headers=auth_headers)
    rule_id = create_resp.json()["id"]

    # Trigger an event to generate logs
    from backend.models.member import Member
    member = Member(name="日志会员", phone="13900004444", organization_id=1)
    db.add(member)
    await db.commit()

    await client.post("/api/v1/marketing/events", json={
        "event_type": "member_created",
        "entity_id": member.id,
    }, headers=auth_headers)

    # Get logs
    resp = await client.get(f"/api/v1/marketing/rules/{rule_id}/logs", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_list_rules_filter_active(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/marketing/rules", json={
        "name": "活跃规则",
        "trigger": {"event_type": "member_created"},
        "actions": [{"type": "send_notification", "params": {}}],
        "is_active": True,
    }, headers=auth_headers)

    resp = await client.get("/api/v1/marketing/rules", params={"is_active": "true"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # All returned rules should be active
    for rule in data["data"]:
        assert rule["is_active"] is True


@pytest.mark.asyncio
async def test_rule_with_multiple_actions(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/marketing/rules", json={
        "name": "多动作规则",
        "trigger": {"event_type": "member_created"},
        "conditions": [],
        "actions": [
            {"type": "send_notification", "params": {"title": "通知", "content": "内容"}},
            {"type": "add_tag", "params": {"tags": ["新会员"]}},
        ],
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["actions"]) == 2


@pytest.mark.asyncio
async def test_rule_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/marketing/rules/99999", headers=auth_headers)
    assert resp.status_code == 404

    resp = await client.put("/api/v1/marketing/rules/99999", json={"name": "x"}, headers=auth_headers)
    assert resp.status_code == 404

    resp = await client.delete("/api/v1/marketing/rules/99999", headers=auth_headers)
    assert resp.status_code == 404
