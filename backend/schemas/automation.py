from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from backend.models.automation import AutomationTriggerType, AutomationActionType


class AutomationRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: AutomationTriggerType
    trigger_config: Optional[dict] = None
    action_type: AutomationActionType = AutomationActionType.SEND_NOTIFICATION
    action_config: Optional[dict] = None


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[AutomationTriggerType] = None
    trigger_config: Optional[dict] = None
    action_type: Optional[AutomationActionType] = None
    action_config: Optional[dict] = None
    is_active: Optional[bool] = None


class AutomationRuleResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    description: Optional[str] = None
    trigger_type: AutomationTriggerType
    trigger_config: Optional[dict] = None
    action_type: AutomationActionType
    action_config: Optional[dict] = None
    is_active: bool
    execution_count: int
    last_executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AutomationLogResponse(BaseModel):
    id: int
    rule_id: int
    trigger_entity_type: str
    trigger_entity_id: Optional[int] = None
    action_result: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
