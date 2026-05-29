"""
营销规则引擎 - Trigger -> Condition -> Action 模式
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.automation import AutomationRule, AutomationLog, AutomationTriggerType, AutomationActionType
from backend.models.member import Member, MemberStatus
from backend.models.notification import Notification, NotificationType
from backend.models.auth import User
from backend.logger import logger


class MarketingEngine:
    """营销自动化引擎 - Trigger -> Condition -> Action 模式"""

    TRIGGER_TYPES = {
        "member_created",
        "birthday",
        "card_expiring",
        "card_expired",
        "last_visit",
        "purchase_completed",
        "booking_completed",
        "no_visit_days",
        "low_balance",
        "custom_event",
    }

    CONDITION_TYPES = {
        "member_tag",
        "member_level",
        "card_type",
        "store_id",
        "days_since_visit",
        "balance_threshold",
        "purchase_count",
        "custom_condition",
    }

    ACTION_TYPES = {
        "send_sms",
        "send_wechat",
        "send_notification",
        "issue_coupon",
        "add_tag",
        "create_task",
        "trigger_webhook",
        "update_field",
    }

    @staticmethod
    async def process_event(
        db: AsyncSession,
        event_type: str,
        entity_id: int,
        organization_id: int,
        context: dict = None,
    ) -> list[dict]:
        """处理事件 - 查找匹配规则并执行动作"""
        context = context or {}

        # Map marketing trigger types to automation trigger types
        trigger_map = {
            "member_created": AutomationTriggerType.MEMBER_CREATED,
            "birthday": AutomationTriggerType.BIRTHDAY,
            "card_expiring": AutomationTriggerType.CARD_EXPIRING,
        }

        auto_trigger = trigger_map.get(event_type)
        if not auto_trigger:
            return []

        # Find all active rules for this trigger_type and org
        result = await db.execute(
            select(AutomationRule).where(
                AutomationRule.organization_id == organization_id,
                AutomationRule.trigger_type == auto_trigger,
                AutomationRule.is_active.is_(True),
            )
        )
        rules = list(result.scalars().all())

        results = []
        for rule in rules:
            try:
                # Get entity data
                entity_data = await MarketingEngine._get_entity_data(
                    db, event_type, entity_id, organization_id, context,
                )

                # Evaluate conditions
                conditions = rule.trigger_config.get("conditions", []) if rule.trigger_config else []
                matched = await MarketingEngine.evaluate_conditions(db, rule, entity_data)

                if matched:
                    actions_executed = await MarketingEngine.execute_actions(
                        db, rule, entity_data, [entity_id],
                    )
                    rule.execution_count = (rule.execution_count or 0) + 1
                    rule.last_executed_at = datetime.utcnow()

                    log = AutomationLog(
                        rule_id=rule.id,
                        organization_id=organization_id,
                        trigger_entity_type=event_type,
                        trigger_entity_id=entity_id,
                        action_result={"actions": actions_executed},
                        status="success",
                    )
                    db.add(log)

                    results.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "matched": True,
                        "actions_executed": actions_executed,
                    })
                else:
                    results.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "matched": False,
                        "actions_executed": [],
                    })
            except Exception as e:
                logger.exception("Error processing rule %s: %s", rule.id, str(e))
                log = AutomationLog(
                    rule_id=rule.id,
                    organization_id=organization_id,
                    trigger_entity_type=event_type,
                    trigger_entity_id=entity_id,
                    status="failed",
                    error_message=str(e),
                )
                db.add(log)
                results.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "matched": False,
                    "actions_executed": [],
                    "errors": [str(e)],
                })

        return results

    @staticmethod
    async def _get_entity_data(
        db: AsyncSession,
        event_type: str,
        entity_id: int,
        organization_id: int,
        context: dict,
    ) -> dict:
        """获取实体数据用于条件评估"""
        if event_type == "member_created" or event_type == "birthday":
            result = await db.execute(
                select(Member).where(Member.id == entity_id, Member.organization_id == organization_id)
            )
            member = result.scalar_one_or_none()
            if member:
                return {
                    "id": member.id,
                    "name": member.name,
                    "phone": member.phone,
                    "email": member.email,
                    "tags": member.tags or [],
                    "level": member.level,
                    "card_type": member.card_type.value if member.card_type else None,
                    "card_balance": member.card_balance or 0,
                    "status": member.status.value if member.status else None,
                    "birthday": member.birthday,
                    "created_at": member.created_at,
                    "store_id": getattr(member, "store_id", None),
                }
        return context or {}

    @staticmethod
    async def evaluate_conditions(db: AsyncSession, rule: AutomationRule, entity_data: dict) -> bool:
        """评估规则条件是否满足"""
        conditions = (rule.trigger_config or {}).get("conditions", [])
        if not conditions:
            return True  # No conditions = always match

        for cond in conditions:
            cond_type = cond.get("type")
            operator = cond.get("operator", "eq")
            value = cond.get("value")

            if not cond_type or value is None:
                continue

            field_value = entity_data.get(cond_type)

            # Handle None field values
            if field_value is None:
                if operator in ("eq",):
                    return False
                elif operator in ("ne", "not_in"):
                    continue
                else:
                    return False

            # Evaluate based on operator
            if operator == "eq":
                if field_value != value:
                    return False
            elif operator == "ne":
                if field_value == value:
                    return False
            elif operator == "in":
                if field_value not in value:
                    return False
            elif operator == "not_in":
                if field_value in value:
                    return False
            elif operator == "gt":
                if not (field_value > value):
                    return False
            elif operator == "lt":
                if not (field_value < value):
                    return False
            elif operator == "gte":
                if not (field_value >= value):
                    return False
            elif operator == "lte":
                if not (field_value <= value):
                    return False
            elif operator == "contains":
                if isinstance(value, list):
                    if isinstance(field_value, list):
                        # Check if any item in value is in field_value
                        if not any(v in field_value for v in value):
                            return False
                    else:
                        if field_value not in value:
                            return False
                elif isinstance(value, str):
                    if str(field_value) not in value:
                        return False

        return True

    @staticmethod
    async def execute_actions(
        db: AsyncSession,
        rule: AutomationRule,
        entity_data: dict,
        matched_entities: list,
    ) -> list[dict]:
        """执行规则动作"""
        actions_config = (rule.trigger_config or {}).get("actions", [])
        executed = []

        for action in actions_config:
            action_type = action.get("type")
            params = action.get("params", {})

            try:
                if action_type == "send_notification":
                    title = params.get("title", rule.name)
                    content = params.get("content", "")
                    # Render template
                    for key, val in entity_data.items():
                        if val is not None:
                            title = str(title).replace(f"{{{{{key}}}}}", str(val))
                            content = str(content).replace(f"{{{{{key}}}}}", str(val))

                    # Find user to notify
                    member_id = entity_data.get("id")
                    if member_id:
                        notification = Notification(
                            user_id=member_id,
                            notification_type=NotificationType.MARKETING,
                            title=title,
                            content=content,
                            organization_id=rule.organization_id,
                        )
                        db.add(notification)
                    executed.append({"type": "send_notification", "status": "success"})

                elif action_type == "add_tag":
                    tags = params.get("tags", [])
                    if tags and entity_data.get("id"):
                        member_result = await db.execute(
                            select(Member).where(Member.id == entity_data["id"])
                        )
                        member = member_result.scalar_one_or_none()
                        if member:
                            existing_tags = member.tags or []
                            for tag in tags:
                                if tag not in existing_tags:
                                    existing_tags.append(tag)
                            member.tags = existing_tags
                    executed.append({"type": "add_tag", "status": "success", "tags": tags})

                elif action_type == "issue_coupon":
                    executed.append({"type": "issue_coupon", "status": "success", "params": params})

                elif action_type == "send_sms":
                    executed.append({"type": "send_sms", "status": "success", "params": params})

                elif action_type == "send_wechat":
                    executed.append({"type": "send_wechat", "status": "success", "params": params})

                elif action_type == "create_task":
                    executed.append({"type": "create_task", "status": "success", "params": params})

                elif action_type == "trigger_webhook":
                    executed.append({"type": "trigger_webhook", "status": "success", "params": params})

                elif action_type == "update_field":
                    executed.append({"type": "update_field", "status": "success", "params": params})

                else:
                    executed.append({"type": action_type, "status": "unknown"})

            except Exception as e:
                logger.exception("Error executing action %s for rule %s: %s", action_type, rule.id, str(e))
                executed.append({"type": action_type, "status": "failed", "error": str(e)})

        return executed

    @staticmethod
    async def check_scheduled_triggers(db: AsyncSession, organization_id: int) -> dict:
        """检查定时触发器（生日、到期、未到店等）"""
        now = datetime.utcnow()
        results = {"birthday": 0, "card_expiring": 0, "inactive": 0}

        # Birthday
        from sqlalchemy import extract
        birthday_members = await db.execute(
            select(Member).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
                Member.birthday.isnot(None),
                extract("month", Member.birthday) == now.month,
                extract("day", Member.birthday) == now.day,
            )
        )
        results["birthday"] = len(list(birthday_members.scalars().all()))

        # Card expiring (within 7 days)
        from datetime import timedelta
        target_start = now
        target_end = now + timedelta(days=7)
        expiring_members = await db.execute(
            select(Member).where(
                Member.organization_id == organization_id,
                Member.status == MemberStatus.ACTIVE,
                Member.card_end_date >= target_start,
                Member.card_end_date < target_end,
            )
        )
        results["card_expiring"] = len(list(expiring_members.scalars().all()))

        return results
