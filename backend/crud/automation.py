from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.automation import AutomationRule, AutomationLog, AutomationTriggerType
from backend.schemas.automation import AutomationRuleCreate, AutomationRuleUpdate


class AutomationCRUD:
    @staticmethod
    async def create(
        db: AsyncSession, obj_in: AutomationRuleCreate, organization_id: int,
    ) -> AutomationRule:
        rule = AutomationRule(
            name=obj_in.name,
            description=obj_in.description,
            trigger_type=obj_in.trigger_type,
            trigger_config=obj_in.trigger_config,
            action_type=obj_in.action_type,
            action_config=obj_in.action_config,
            organization_id=organization_id,
        )
        db.add(rule)
        await db.flush()
        return rule

    @staticmethod
    async def get(
        db: AsyncSession, rule_id: int, organization_id: int,
    ) -> Optional[AutomationRule]:
        result = await db.execute(
            select(AutomationRule).where(
                AutomationRule.id == rule_id,
                AutomationRule.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession, rule: AutomationRule, obj_in: AutomationRuleUpdate,
    ) -> AutomationRule:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
        await db.flush()
        return rule

    @staticmethod
    async def delete(db: AsyncSession, rule: AutomationRule) -> None:
        await db.delete(rule)

    @staticmethod
    async def get_list(
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        trigger_type: Optional[AutomationTriggerType] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[AutomationRule], int]:
        query = select(AutomationRule).where(
            AutomationRule.organization_id == organization_id,
        )
        if trigger_type:
            query = query.where(AutomationRule.trigger_type == trigger_type)
        if is_active is not None:
            query = query.where(AutomationRule.is_active == is_active)
        total_result = await db.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total = total_result.scalar()
        result = await db.execute(
            query.order_by(AutomationRule.created_at.desc())
            .offset(skip).limit(limit),
        )
        return list(result.scalars().all()), total or 0

    @staticmethod
    async def get_active_by_trigger(
        db: AsyncSession, organization_id: int, trigger_type: AutomationTriggerType,
    ) -> list[AutomationRule]:
        result = await db.execute(
            select(AutomationRule).where(
                AutomationRule.organization_id == organization_id,
                AutomationRule.trigger_type == trigger_type,
                AutomationRule.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def log_execution(
        db: AsyncSession, rule_id: int, organization_id: int,
        entity_type: str, entity_id: Optional[int] = None,
        status: str = "success", error_message: Optional[str] = None,
        action_result: Optional[dict] = None,
    ) -> AutomationLog:
        log = AutomationLog(
            rule_id=rule_id,
            organization_id=organization_id,
            trigger_entity_type=entity_type,
            trigger_entity_id=entity_id,
            action_result=action_result,
            status=status,
            error_message=error_message,
        )
        db.add(log)
        return log

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        organization_id: int,
        rule_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AutomationLog], int]:
        query = select(AutomationLog).where(
            AutomationLog.organization_id == organization_id,
        )
        if rule_id:
            query = query.where(AutomationLog.rule_id == rule_id)
        total_result = await db.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total = total_result.scalar()
        result = await db.execute(
            query.order_by(AutomationLog.created_at.desc())
            .offset(skip).limit(limit),
        )
        return list(result.scalars().all()), total or 0
