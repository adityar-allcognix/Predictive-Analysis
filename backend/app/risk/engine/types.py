from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PolicyInput:
    policy_id: str
    policy_number: str
    insured_id: str
    product_line: str
    region_code: str
    asset_type: str
    asset_value: float
    coverage_limit: float
    deductible: float
    effective_date: date
    expiry_date: date


@dataclass(frozen=True)
class ClaimsSummaryInput:
    lookback_months: int
    claim_count: int
    total_paid_amount: float
    total_reserved_amount: float


@dataclass(frozen=True)
class TelematicsAggregateInput:
    period_start: date
    period_end: date
    miles_driven: float
    harsh_braking_events: int
    speeding_events: int
    distracted_driving_events: int
    night_driving_pct: float


@dataclass(frozen=True)
class IoTAssetMetricInput:
    captured_at: datetime
    device_id: str
    health_score: int
    anomaly_count: int


@dataclass(frozen=True)
class ClimateIndexInput:
    region_code: str
    peril_type: str
    index_date: date
    hazard_index: int


@dataclass(frozen=True)
class RiskInputBundle:
    policy: PolicyInput
    claims: ClaimsSummaryInput
    telematics: Optional[TelematicsAggregateInput]
    iot: Optional[IoTAssetMetricInput]
    climate: Optional[ClimateIndexInput]


@dataclass(frozen=True)
class RiskComponentResult:
    component_name: str
    raw_value: Optional[float]
    normalized_score: int  # 0..100
    weight: float
    weighted_score: float
    details: Dict[str, Any]


@dataclass(frozen=True)
class PreventiveActionResult:
    rule_id: str
    action_type: str
    priority: int
    action_payload: Dict[str, Any]
    rationale: str


@dataclass(frozen=True)
class RiskEvaluationResult:
    loss_risk_index: int
    risk_band: str
    components: List[RiskComponentResult]
    fired_rules: List[str]
    preventive_actions: List[PreventiveActionResult]
    explanation: Dict[str, Any]
