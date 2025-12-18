from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from app.risk.engine.types import RiskEvaluationResult

from .auto_engine import AUTO_RULESET_PATH, evaluate_auto
from .health_engine import HEALTH_RULESET_PATH, evaluate_health
from .life_engine import LIFE_RULESET_PATH, evaluate_life
from .health_types import HealthRiskInputBundle
from .life_types import LifeRiskInputBundle


ALLOWED_POLICY_TYPES = {"AUTO", "HLTH", "LIFE"}


def parse_policy_type_from_policy_number(policy_number: str) -> str:
    prefix = (policy_number or "").split("-", 1)[0].strip().upper()
    if prefix not in ALLOWED_POLICY_TYPES:
        raise ValueError(f"Invalid policy_number prefix: {prefix}. Expected one of {sorted(ALLOWED_POLICY_TYPES)}")
    return prefix


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_by_policy_type(
    *,
    policy_type: str,
    inputs: Any,
) -> Tuple[RiskEvaluationResult, Dict[str, Any], Path]:
    pt = (policy_type or "").upper()
    if pt == "AUTO":
        evaluation, ruleset = evaluate_auto(inputs)
        return evaluation, ruleset, AUTO_RULESET_PATH

    if pt == "HLTH":
        if not isinstance(inputs, HealthRiskInputBundle):
            raise ValueError("HLTH evaluation requires HealthRiskInputBundle")
        ruleset = _load_json(HEALTH_RULESET_PATH)
        evaluation = evaluate_health(inputs, ruleset)
        return evaluation, ruleset, HEALTH_RULESET_PATH

    if pt == "LIFE":
        if not isinstance(inputs, LifeRiskInputBundle):
            raise ValueError("LIFE evaluation requires LifeRiskInputBundle")
        ruleset = _load_json(LIFE_RULESET_PATH)
        evaluation = evaluate_life(inputs, ruleset)
        return evaluation, ruleset, LIFE_RULESET_PATH

    raise ValueError(f"Unsupported policy_type: {policy_type}")
