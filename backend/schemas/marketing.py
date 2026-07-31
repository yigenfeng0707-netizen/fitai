"""
Pydantic Schema - 营销规则引擎
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class RuleTriggerConfig(BaseModel):
    event_type: str
    filters: Optional[dict] = None


class RuleConditionConfig(BaseModel):
    type: str  # member_tag, member_level, etc.
    operator: str  # eq, ne, in, not_in, gt, lt, gte, lte, contains
    value: Any


class RuleActionConfig(BaseModel):
    type: str  # send_sms, issue_coupon, etc.
    params: dict  # action-specific parameters
    delay_seconds: int = 0


class MarketingRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger: RuleTriggerConfig
    conditions: list[RuleConditionConfig] = []
    actions: list[RuleActionConfig]
    is_active: bool = True


class MarketingRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[RuleTriggerConfig] = None
    conditions: Optional[list[RuleConditionConfig]] = None
    actions: Optional[list[RuleActionConfig]] = None
    is_active: Optional[bool] = None


class MarketingRuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: dict
    conditions: list[dict]
    actions: list[dict]
    is_active: bool
    execution_count: int
    last_executed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventRequest(BaseModel):
    event_type: str
    entity_id: int
    context: Optional[dict] = None


class ExecutionResult(BaseModel):
    rule_id: int
    rule_name: str
    matched: bool
    actions_executed: list[dict] = []
    errors: list[str] = []
