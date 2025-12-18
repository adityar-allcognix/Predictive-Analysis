from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.risk.engine.rule_eval import apply_rules
from app.risk.engine.types import PreventiveActionResult, RiskComponentResult, RiskEvaluationResult

from .life_types import LifeRiskInputBundle


LIFE_RULESET_PATH = Path(__file__).resolve().parents[1] / "rules" / "life_ruleset_v1.json"


def _clamp_int(value: float, min_v: int = 0, max_v: int = 100) -> int:
    if value < min_v:
        return min_v
    if value > max_v:
        return max_v
    return int(round(value))


def _tier_score(value: float, low: float, medium: float, high: float) -> int:
    if value <= low:
        return 20
    if value <= medium:
        return 50
    if value <= high:
        return 80
    return 100


def _assign_band(lri: int, ruleset: Dict[str, Any]) -> str:
    score = _clamp_int(float(lri), 0, 100)
    for band in ruleset.get("risk_bands", []):
        if int(band["min"]) <= score <= int(band["max"]):
            return str(band["band"])
    return "MEDIUM"


def _tenure_risk_score(tenure_years: int, new_max: int, mid_max: int) -> int:
    t = max(0, int(tenure_years))
    if t <= new_max:
        return 70
    if t <= mid_max:
        return 40
    return 20


def _compute_components(inputs: LifeRiskInputBundle, ruleset: Dict[str, Any]) -> List[RiskComponentResult]:
    weights = ruleset["weights"]

    age_cfg = ruleset["components"]["age_risk"]
    insured_age = max(0, int(inputs.profile.insured_age))
    age_score = _tier_score(insured_age, float(age_cfg["low"]), float(age_cfg["medium"]), float(age_cfg["high"]))

    tenure_cfg = ruleset["components"]["tenure_years"]
    tenure_score = _tenure_risk_score(int(inputs.tenure_years), int(tenure_cfg["new_max"]), int(tenure_cfg["mid_max"]))

    mortality_score = _clamp_int(float(inputs.mortality_index), 0, 100)

    components: List[RiskComponentResult] = []

    w_age = float(weights["age_risk"])
    components.append(
        RiskComponentResult(
            component_name="age_risk",
            raw_value=float(insured_age),
            normalized_score=_clamp_int(age_score),
            weight=w_age,
            weighted_score=w_age * _clamp_int(age_score),
            details={"insured_age": insured_age, "thresholds": {"low": age_cfg["low"], "medium": age_cfg["medium"], "high": age_cfg["high"]}},
        )
    )

    w_tenure = float(weights["tenure_risk"])
    components.append(
        RiskComponentResult(
            component_name="tenure_risk",
            raw_value=float(int(inputs.tenure_years)),
            normalized_score=_clamp_int(tenure_score),
            weight=w_tenure,
            weighted_score=w_tenure * _clamp_int(tenure_score),
            details={"tenure_years": int(inputs.tenure_years), "new_max": int(tenure_cfg["new_max"]), "mid_max": int(tenure_cfg["mid_max"])},
        )
    )

    w_mort = float(weights["mortality_index"])
    components.append(
        RiskComponentResult(
            component_name="mortality_index",
            raw_value=float(mortality_score),
            normalized_score=mortality_score,
            weight=w_mort,
            weighted_score=w_mort * mortality_score,
            details={"mortality_index": mortality_score},
        )
    )

    return components


def _compute_lri(components: List[RiskComponentResult]) -> int:
    total_weight = sum(c.weight for c in components)
    if total_weight <= 0:
        return 0
    weighted_sum = sum(c.weighted_score for c in components)
    return _clamp_int(weighted_sum / total_weight, 0, 100)


def evaluate_life(inputs: LifeRiskInputBundle, ruleset: Dict[str, Any]) -> RiskEvaluationResult:
    components = _compute_components(inputs, ruleset)
    lri = _compute_lri(components)
    band = _assign_band(lri, ruleset)

    context = {
        "risk": {"lri": lri, "band": band},
        "components": {c.component_name: asdict(c) for c in components},
        "inputs": {
            "policy": asdict(inputs.policy),
            "profile": asdict(inputs.profile),
            "tenure_years": int(inputs.tenure_years),
            "mortality_index": int(inputs.mortality_index),
        },
    }

    fired_rules, actions = apply_rules(ruleset, context)

    explanation: Dict[str, Any] = {
        "policy": {"policy_type": "LIFE", "policy_number": inputs.policy.policy_number},
        "model": {"ruleset_name": ruleset.get("ruleset_name"), "version": ruleset.get("version")},
        "summary": {
            "loss_risk_index": lri,
            "risk_band": band,
            "component_scores": {c.component_name: c.normalized_score for c in components},
            "fired_rules": fired_rules,
        },
        "type_notes": [
            "LIFE: Uses insured age, policy tenure, and a static mortality index table.",
            "LIFE: No telematics/IoT/climate factors are considered.",
        ],
    }

    fired_rules_sorted = list(fired_rules)
    actions_sorted: List[PreventiveActionResult] = sorted(actions, key=lambda a: (int(a.priority), str(a.action_type), str(a.rule_id)))

    return RiskEvaluationResult(
        loss_risk_index=lri,
        risk_band=band,
        components=components,
        fired_rules=fired_rules_sorted,
        preventive_actions=actions_sorted,
        explanation=explanation,
    )
