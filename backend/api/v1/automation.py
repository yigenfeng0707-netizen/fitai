"""API - 营销自动化"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.auth import User
from backend.schemas.automation import (
    AutomationRuleCreate, AutomationRuleUpdate, AutomationRuleResponse, AutomationLogResponse,
)
from backend.crud.automation import AutomationCRUD
from backend.services.automation_engine import AutomationEngine

router = APIRouter()


@router.get("/", response_model=dict)
async def list_rules(
    skip: int = 0,
    limit: int = 20,
    trigger_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query_trigger = None
    if trigger_type:
        from backend.models.automation import AutomationTriggerType
        try:
            query_trigger = AutomationTriggerType(trigger_type)
        except ValueError:
            pass
    rules, total = await AutomationCRUD.get_list(
        db, organization_id=current_user.organization_id,
        skip=skip, limit=limit, trigger_type=query_trigger,
    )
    return {
        "success": True, "message": "ok",
        "data": [AutomationRuleResponse.model_validate(r).model_dump() for r in rules],
        "total": total,
    }


@router.post("/", response_model=dict, status_code=201)
async def create_rule(
    obj_in: AutomationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = await AutomationCRUD.create(
        db, obj_in, organization_id=current_user.organization_id,
    )
    return {
        "success": True, "message": "创建成功",
        "data": AutomationRuleResponse.model_validate(rule).model_dump(),
    }


@router.get("/{rule_id}", response_model=dict)
async def get_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = await AutomationCRUD.get(db, rule_id, organization_id=current_user.organization_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return {
        "success": True, "message": "ok",
        "data": AutomationRuleResponse.model_validate(rule).model_dump(),
    }


@router.put("/{rule_id}", response_model=dict)
async def update_rule(
    rule_id: int,
    obj_in: AutomationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = await AutomationCRUD.get(db, rule_id, organization_id=current_user.organization_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    rule = await AutomationCRUD.update(db, rule, obj_in)
    return {
        "success": True, "message": "更新成功",
        "data": AutomationRuleResponse.model_validate(rule).model_dump(),
    }


@router.delete("/{rule_id}", response_model=dict)
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = await AutomationCRUD.get(db, rule_id, organization_id=current_user.organization_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    await AutomationCRUD.delete(db, rule)
    return {"success": True, "message": "删除成功"}


@router.post("/{rule_id}/toggle", response_model=dict)
async def toggle_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = await AutomationCRUD.get(db, rule_id, organization_id=current_user.organization_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    rule.is_active = not rule.is_active
    await db.flush()
    return {
        "success": True, "message": "操作成功",
        "data": AutomationRuleResponse.model_validate(rule).model_dump(),
    }


@router.get("/logs/list", response_model=dict)
async def list_logs(
    rule_id: int = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs, total = await AutomationCRUD.get_logs(
        db, organization_id=current_user.organization_id,
        rule_id=rule_id, skip=skip, limit=limit,
    )
    return {
        "success": True, "message": "ok",
        "data": [AutomationLogResponse.model_validate(log).model_dump() for log in logs],
        "total": total,
    }


@router.post("/check-time-triggers", response_model=dict)
async def check_time_triggers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = await AutomationEngine.check_time_based_triggers(
        db, organization_id=current_user.organization_id,
    )
    return {"success": True, "message": f"已检查并执行 {len(results)} 条规则", "data": results}
