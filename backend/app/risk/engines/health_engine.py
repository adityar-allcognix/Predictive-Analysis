from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.risk.engine.rule_eval import apply_rules
from app.risk.engine.types import PreventiveActionResult, RiskComponentResult, RiskEvaluationResult

from .health_types import HealthRiskInputBundle


HEALTH_RULESET_PATH = Path(__file__).resolve().parents[1] / "rules" / "health_ruleset_v1.json"


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


def _compute_components(inputs: HealthRiskInputBundle, ruleset: Dict[str, Any]) -> List[RiskComponentResult]:
    weights = ruleset["weights"]

    age_cfg = ruleset["components"]["age_risk"]
    member_age = max(0, int(inputs.profile.member_age))
    age_score = _tier_score(member_age, float(age_cfg["low"]), float(age_cfg["medium"]), float(age_cfg["high"]))
    age_details = {"member_age": member_age, "thresholds": {"low": age_cfg["low"], "medium": age_cfg["medium"], "high": age_cfg["high"]}}

    sev_cfg = ruleset["components"]["claims_severity"]
    severity_amount = max(0.0, float(inputs.claims.total_paid_amount)) + max(0.0, float(inputs.claims.total_reserved_amount))
    sev_score = _tier_score(severity_amount, float(sev_cfg["low_usd"]), float(sev_cfg["medium_usd"]), float(sev_cfg["high_usd"]))
    sev_details = {"severity_amount": severity_amount, "lookback_months": int(inputs.claims.lookback_months)}

    chronic_cfg = ruleset["components"]["chronic_indicators"]
    chronic_flags = inputs.profile.chronic_flags or {}
    chronic_count = sum(1 for _, v in chronic_flags.items() if bool(v))
    if chronic_count <= 0:
        chronic_score = int(chronic_cfg["none_score"])
    elif chronic_count == 1:
        chronic_score = int(chronic_cfg["one_score"])
    elif chronic_count == 2:
        chronic_score = int(chronic_cfg["two_score"])
    else:
        chronic_score = int(chronic_cfg["three_plus_score"])
    chronic_details = {"chronic_count": chronic_count, "chronic_flags": chronic_flags}

    components: List[RiskComponentResult] = []

    w_age = float(weights["age_risk"])
    components.append(
        RiskComponentResult(
            component_name="age_risk",
            raw_value=float(member_age),
            normalized_score=_clamp_int(age_score),
            weight=w_age,
            weighted_score=w_age * _clamp_int(age_score),
            details=age_details,
        )
    )

    w_sev = float(weights["claims_severity"])
    components.append(
        RiskComponentResult(
            component_name="claims_severity",
            raw_value=float(severity_amount),
            normalized_score=_clamp_int(sev_score),
            weight=w_sev,
            weighted_score=w_sev * _clamp_int(sev_score),
            details=sev_details,
        )
    )

    w_chr = float(weights["chronic_indicators"])
    components.append(
        RiskComponentResult(
            component_name="chronic_indicators",
            raw_value=float(chronic_count),
            normalized_score=_clamp_int(chronic_score),
            weight=w_chr,
            weighted_score=w_chr * _clamp_int(chronic_score),
            details=chronic_details,
        )
    )

    return components


def _compute_lri(components: List[RiskComponentResult]) -> int:
    total_weight = sum(c.weight for c in components)
    if total_weight <= 0:
        return 0
    weighted_sum = sum(c.weighted_score for c in components)
    return _clamp_int(weighted_sum / total_weight, 0, 100)


def evaluate_health(inputs: HealthRiskInputBundle, ruleset: Dict[str, Any]) -> RiskEvaluationResult:
    components = _compute_components(inputs, ruleset)
    lri = _compute_lri(components)
    band = _assign_band(lri, ruleset)

    context = {
        "risk": {"lri": lri, "band": band},
        "components": {c.component_name: asdict(c) for c in components},
        "inputs": {"policy": asdict(inputs.policy), "claims": asdict(inputs.claims), "profile": asdict(inputs.profile)},
    }

    fired_rules, actions = apply_rules(ruleset, context)

    explanation: Dict[str, Any] = {
        "policy": {"policy_type": "HLTH", "policy_number": inputs.policy.policy_number},
        "model": {"ruleset_name": ruleset.get("ruleset_name"), "version": ruleset.get("version")},
        "summary": {
            "loss_risk_index": lri,
            "risk_band": band,
            "component_scores": {c.component_name: c.normalized_score for c in components},
            "fired_rules": fired_rules,
        },
        "type_notes": [
            "HLTH: Uses member age, claims severity, and chronic indicators.",
            "HLTH: No telematics/IoT/climate factors are considered.",
        ],
    }

    # Enforce deterministic ordering for auditability.
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
