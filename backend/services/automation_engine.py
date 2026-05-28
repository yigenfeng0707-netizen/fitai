"""营销自动化引擎"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.automation import AutomationRule, AutomationTriggerType, AutomationActionType
from backend.models.member import Member, MemberStatus
from backend.models.lead import Lead
from backend.models.notification import NotificationType, Notification
from backend.models.auth import User
from backend.crud.automation import AutomationCRUD


class AutomationEngine:

    @staticmethod
    async def execute_rules_for_trigger(
        db: AsyncSession,
        organization_id: int,
        trigger_type: AutomationTriggerType,
        entity_type: str,
        entity_id: Optional[int] = None,
        context: Optional[dict] = None,
    ) -> list[dict]:
        rules = await AutomationCRUD.get_active_by_trigger(
            db, organization_id, trigger_type,
        )
        results = []
        for rule in rules:
            result = await AutomationEngine._execute_rule(
                db, rule, entity_type, entity_id, context or {},
            )
            results.append(result)
        return results

    @staticmethod
    async def _execute_rule(
        db: AsyncSession,
        rule: AutomationRule,
        entity_type: str,
        entity_id: Optional[int],
        context: dict,
    ) -> dict:
        try:
            if rule.action_type == AutomationActionType.SEND_NOTIFICATION:
                await AutomationEngine._action_send_notification(
                    db, rule, entity_type, entity_id, context,
                )

            rule.execution_count = (rule.execution_count or 0) + 1
            rule.last_executed_at = datetime.utcnow()

            await AutomationCRUD.log_execution(
                db, rule.id, rule.organization_id,
                entity_type, entity_id,
                status="success",
            )
            return {"rule_id": rule.id, "status": "success"}
        except Exception as e:
            await AutomationCRUD.log_execution(
                db, rule.id, rule.organization_id,
                entity_type, entity_id,
                status="failed", error_message=str(e),
            )
            return {"rule_id": rule.id, "status": "failed", "error": str(e)}

    @staticmethod
    async def _action_send_notification(
        db: AsyncSession,
        rule: AutomationRule,
        entity_type: str,
        entity_id: Optional[int],
        context: dict,
    ) -> None:
        config = rule.action_config or {}
        title_template = config.get("title", rule.name)
        content_template = config.get("content", "")
        notification_type_str = config.get("notification_type", "system")

        title = AutomationEngine._render_template(title_template, context)
        content = AutomationEngine._render_template(content_template, context)

        try:
            notification_type = NotificationType(notification_type_str)
        except ValueError:
            notification_type = NotificationType.SYSTEM

        target_users = config.get("target_users", ["member"])
        user_ids = await AutomationEngine._resolve_target_users(
            db, rule.organization_id, target_users, entity_type, entity_id,
        )

        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                content=content,
                organization_id=rule.organization_id,
            )
            db.add(notification)

    @staticmethod
    async def _resolve_target_users(
        db: AsyncSession,
        organization_id: int,
        target_users: list[str],
        entity_type: str,
        entity_id: Optional[int],
    ) -> list[int]:
        user_ids = set()
        for target in target_users:
            if target == "member" and entity_id:
                member_result = await db.execute(
                    select(Member).where(Member.id == entity_id)
                )
                member = member_result.scalar_one_or_none()
                if member and member.coach_id:
                    coach_user = await db.execute(
                        select(User).where(
                            User.coach_id == member.coach_id,
                            User.organization_id == organization_id,
                        )
                    )
                    if coach_user.scalar_one_or_none():
                        user_ids.add(coach_user.scalar_one().id)
            elif target == "lead_assignee" and entity_id:
                lead_result = await db.execute(
                    select(Lead).where(Lead.id == entity_id)
                )
                lead = lead_result.scalar_one_or_none()
                if lead and lead.assigned_to:
                    user_ids.add(lead.assigned_to)
            elif target == "admins":
                admins = await db.execute(
                    select(User.id).where(
                        User.organization_id == organization_id,
                        User.is_active.is_(True),
                        User.role.in_(["super_admin", "store_owner"]),
                    )
                )
                for row in admins:
                    user_ids.add(row[0])
        return list(user_ids)

    @staticmethod
    def _render_template(template: str, context: dict) -> str:
        result = template
        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))
        return result

    @staticmethod
    async def check_time_based_triggers(db: AsyncSession, organization_id: int) -> list[dict]:
        now = datetime.utcnow()
        results = []

        birthday_rules = await AutomationCRUD.get_active_by_trigger(
            db, organization_id, AutomationTriggerType.BIRTHDAY,
        )
        if birthday_rules:
            today = now.strftime("%m-%d")
            members = await db.execute(
                select(Member).where(
                    Member.organization_id == organization_id,
                    Member.status == MemberStatus.ACTIVE,
                )
            )
            for member in members.scalars().all():
                if member.birthday and member.birthday.strftime("%m-%d") == today:
                    for rule in birthday_rules:
                        result = await AutomationEngine._execute_rule(
                            db, rule, "member", member.id,
                            {"member_name": member.name, "member_phone": member.phone},
                        )
                        results.append(result)

        expiring_rules = await AutomationCRUD.get_active_by_trigger(
            db, organization_id, AutomationTriggerType.CARD_EXPIRING,
        )
        if expiring_rules:
            for rule in expiring_rules:
                days = (rule.trigger_config or {}).get("days_before", 7)
                target_start = now + timedelta(days=days)
                target_end = target_start + timedelta(days=1)
                members = await db.execute(
                    select(Member).where(
                        Member.organization_id == organization_id,
                        Member.status == MemberStatus.ACTIVE,
                        Member.card_end_date >= target_start,
                        Member.card_end_date < target_end,
                    )
                )
                for member in members.scalars().all():
                    result = await AutomationEngine._execute_rule(
                        db, rule, "member", member.id,
                        {
                            "member_name": member.name,
                            "member_phone": member.phone,
                            "card_end_date": member.card_end_date.strftime("%Y-%m-%d") if member.card_end_date else "",
                        },
                    )
                    results.append(result)

        inactive_rules = await AutomationCRUD.get_active_by_trigger(
            db, organization_id, AutomationTriggerType.MEMBER_INACTIVE,
        )
        if inactive_rules:
            for rule in inactive_rules:
                days = (rule.trigger_config or {}).get("inactive_days", 30)
                cutoff = now - timedelta(days=days)
                members = await db.execute(
                    select(Member).where(
                        Member.organization_id == organization_id,
                        Member.status == MemberStatus.ACTIVE,
                        Member.updated_at < cutoff,
                    )
                )
                for member in members.scalars().all():
                    result = await AutomationEngine._execute_rule(
                        db, rule, "member", member.id,
                        {"member_name": member.name, "member_phone": member.phone, "inactive_days": str(days)},
                    )
                    results.append(result)

        return results

    @staticmethod
    async def on_member_created(db: AsyncSession, organization_id: int, member_id: int, member_name: str, member_phone: str) -> list[dict]:
        return await AutomationEngine.execute_rules_for_trigger(
            db, organization_id, AutomationTriggerType.MEMBER_CREATED,
            "member", member_id,
            {"member_name": member_name, "member_phone": member_phone},
        )

    @staticmethod
    async def on_booking_cancelled(db: AsyncSession, organization_id: int, booking_id: int, context: dict) -> list[dict]:
        return await AutomationEngine.execute_rules_for_trigger(
            db, organization_id, AutomationTriggerType.BOOKING_CANCELLED,
            "booking", booking_id, context,
        )

    @staticmethod
    async def on_lead_created(db: AsyncSession, organization_id: int, lead_id: int, context: dict) -> list[dict]:
        return await AutomationEngine.execute_rules_for_trigger(
            db, organization_id, AutomationTriggerType.LEAD_CREATED,
            "lead", lead_id, context,
        )

    @staticmethod
    async def on_lead_status_changed(db: AsyncSession, organization_id: int, lead_id: int, context: dict) -> list[dict]:
        return await AutomationEngine.execute_rules_for_trigger(
            db, organization_id, AutomationTriggerType.LEAD_STATUS_CHANGED,
            "lead", lead_id, context,
        )
