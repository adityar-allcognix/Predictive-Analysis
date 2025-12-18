from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvaluateRiskRequest(BaseModel):
    policy_number: str = Field(
        ..., description="Policy number: <TYPE>-<REGION>-<YEAR>-<SEQUENCE>"
    )


class RiskComponent(BaseModel):
    component_name: str
    raw_value: Optional[float] = None
    normalized_score: int
    weight: float
    weighted_score: float
    details: Dict[str, Any]


class PreventiveAction(BaseModel):
    rule_id: str
    action_type: str
    priority: int
    action_payload: Dict[str, Any]
    rationale: str


class RiskEvaluationResponse(BaseModel):
    risk_evaluation_id: str
    policy_id: str
    policy_number: str
    policy_type: str
    evaluated_at: datetime
    loss_risk_index: int
    risk_band: str
    rule_version: Dict[str, Any]
    components: List[RiskComponent]
    fired_rules: List[str]
    preventive_actions: List[PreventiveAction]
    input_snapshot: Dict[str, Any]
    explanation: Dict[str, Any]
