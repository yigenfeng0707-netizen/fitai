"""API - 营销规则引擎"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.models.automation import AutomationRule, AutomationLog, AutomationTriggerType, AutomationActionType
from backend.schemas.marketing import (
    MarketingRuleCreate, MarketingRuleUpdate, MarketingRuleResponse,
    EventRequest, ExecutionResult,
)
from backend.schemas.common import ListResponse
from backend.services.marketing_engine import MarketingEngine
from backend.logger import logger

router = APIRouter(prefix="/marketing", tags=["营销自动化"])


def _rule_to_response(rule: AutomationRule) -> dict:
    """Convert AutomationRule to MarketingRuleResponse dict"""
    trigger_config = rule.trigger_config or {}
    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "trigger_type": rule.trigger_type.value if rule.trigger_type else "",
        "trigger_config": trigger_config,
        "conditions": trigger_config.get("conditions", []),
        "actions": trigger_config.get("actions", []),
        "is_active": rule.is_active,
        "execution_count": rule.execution_count or 0,
        "last_executed_at": rule.last_executed_at.isoformat() if rule.last_executed_at else None,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


@router.post("/rules", response_model=MarketingRuleResponse, status_code=201)
async def create_rule(
    rule_in: MarketingRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建营销规则"""
    trigger_map = {
        "member_created": AutomationTriggerType.MEMBER_CREATED,
        "birthday": AutomationTriggerType.BIRTHDAY,
        "card_expiring": AutomationTriggerType.CARD_EXPIRING,
        "booking_cancelled": "booking_cancelled",
        "lead_created": "lead_created",
        "lead_status_changed": "lead_status_changed",
        "member_inactive": "member_inactive",
    }

    trigger_type_str = rule_in.trigger.event_type
    trigger_type = trigger_map.get(trigger_type_str)
    if not trigger_type:
        # Store as string in trigger_config for custom events
        trigger_type = AutomationTriggerType.MEMBER_CREATED

    trigger_config = {
        "event_type": rule_in.trigger.event_type,
        "filters": rule_in.trigger.filters,
        "conditions": [c.model_dump() for c in rule_in.conditions],
        "actions": [a.model_dump() for a in rule_in.actions],
    }

    rule = AutomationRule(
        name=rule_in.name,
        description=rule_in.description,
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        action_type=AutomationActionType.SEND_NOTIFICATION,
        action_config={"actions": [a.model_dump() for a in rule_in.actions]},
        is_active=rule_in.is_active,
        organization_id=current_user.organization_id,
    )
    db.add(rule)
    await db.flush()

    return _rule_to_response(rule)


@router.get("/rules", response_model=ListResponse[MarketingRuleResponse])
async def list_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    trigger_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取规则列表"""
    query = select(AutomationRule).where(AutomationRule.organization_id == current_user.organization_id)
    if is_active is not None:
        query = query.where(AutomationRule.is_active == is_active)
    if trigger_type:
        try:
            tt = AutomationTriggerType(trigger_type)
            query = query.where(AutomationRule.trigger_type == tt)
        except ValueError:
            pass

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    result = await db.execute(
        query.order_by(AutomationRule.created_at.desc()).offset(skip).limit(limit)
    )
    rules = list(result.scalars().all())

    return ListResponse(
        data=[_rule_to_response(r) for r in rules],
        total=total or 0,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/rules/{rule_id}", response_model=MarketingRuleResponse)
async def get_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取规则详情"""
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.organization_id == current_user.organization_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return _rule_to_response(rule)


@router.put("/rules/{rule_id}", response_model=MarketingRuleResponse)
async def update_rule(
    rule_id: int,
    rule_in: MarketingRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新规则"""
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.organization_id == current_user.organization_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if rule_in.name is not None:
        rule.name = rule_in.name
    if rule_in.description is not None:
        rule.description = rule_in.description
    if rule_in.is_active is not None:
        rule.is_active = rule_in.is_active
    if rule_in.trigger is not None:
        trigger_config = rule.trigger_config or {}
        trigger_config["event_type"] = rule_in.trigger.event_type
        trigger_config["filters"] = rule_in.trigger.filters
        rule.trigger_config = trigger_config
    if rule_in.conditions is not None:
        trigger_config = rule.trigger_config or {}
        trigger_config["conditions"] = [c.model_dump() for c in rule_in.conditions]
        rule.trigger_config = trigger_config
    if rule_in.actions is not None:
        trigger_config = rule.trigger_config or {}
        trigger_config["actions"] = [a.model_dump() for a in rule_in.actions]
        rule.trigger_config = trigger_config

    await db.flush()
    return _rule_to_response(rule)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除规则（软删除）"""
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.organization_id == current_user.organization_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    await db.delete(rule)
    return {"success": True, "message": "删除成功"}


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """启用/禁用规则"""
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.organization_id == current_user.organization_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    rule.is_active = not rule.is_active
    await db.flush()
    return {"success": True, "message": "操作成功", "data": _rule_to_response(rule)}


@router.post("/rules/{rule_id}/execute", response_model=list[ExecutionResult])
async def execute_rule_manually(
    rule_id: int,
    event: EventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发规则执行"""
    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.organization_id == current_user.organization_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    results = await MarketingEngine.process_event(
        db,
        event_type=event.event_type,
        entity_id=event.entity_id,
        organization_id=current_user.organization_id,
        context=event.context,
    )

    return [
        ExecutionResult(
            rule_id=r.get("rule_id", rule_id),
            rule_name=r.get("rule_name", rule.name),
            matched=r.get("matched", False),
            actions_executed=r.get("actions_executed", []),
            errors=r.get("errors", []),
        )
        for r in results
    ]


@router.post("/events", response_model=list[ExecutionResult])
async def process_event(
    event: EventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理营销事件"""
    results = await MarketingEngine.process_event(
        db,
        event_type=event.event_type,
        entity_id=event.entity_id,
        organization_id=current_user.organization_id,
        context=event.context,
    )

    return [
        ExecutionResult(
            rule_id=r.get("rule_id", 0),
            rule_name=r.get("rule_name", ""),
            matched=r.get("matched", False),
            actions_executed=r.get("actions_executed", []),
            errors=r.get("errors", []),
        )
        for r in results
    ]


@router.get("/rules/{rule_id}/logs")
async def get_rule_logs(
    rule_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取规则执行日志"""
    query = select(AutomationLog).where(
        AutomationLog.organization_id == current_user.organization_id,
        AutomationLog.rule_id == rule_id,
    )
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    result = await db.execute(
        query.order_by(AutomationLog.created_at.desc()).offset(skip).limit(limit)
    )
    logs = list(result.scalars().all())

    return {
        "success": True,
        "data": [
            {
                "id": log.id,
                "rule_id": log.rule_id,
                "trigger_entity_type": log.trigger_entity_type,
                "trigger_entity_id": log.trigger_entity_id,
                "action_result": log.action_result,
                "status": log.status,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total or 0,
    }


@router.get("/trigger-types")
async def get_trigger_types():
    """获取支持的触发器类型"""
    return {
        "trigger_types": list(MarketingEngine.TRIGGER_TYPES),
    }


@router.get("/action-types")
async def get_action_types():
    """支持的动作类型"""
    return {
        "action_types": list(MarketingEngine.ACTION_TYPES),
    }
