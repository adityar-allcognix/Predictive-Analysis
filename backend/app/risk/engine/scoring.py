from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    ClimateIndexInput,
    ClaimsSummaryInput,
    IoTAssetMetricInput,
    PolicyInput,
    RiskComponentResult,
    RiskInputBundle,
    TelematicsAggregateInput,
)


def _clamp_int(value: float, min_v: int, max_v: int) -> int:
    if value < min_v:
        return min_v
    if value > max_v:
        return max_v
    return int(round(value))


def _safe_div(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else (numerator / denominator)


def _tier_score(value: float, low: float, medium: float, high: float, low_score: int = 20, medium_score: int = 50, high_score: int = 80, extreme_score: int = 100) -> int:
    if value <= low:
        return low_score
    if value <= medium:
        return medium_score
    if value <= high:
        return high_score
    return extreme_score


def load_ruleset(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_claims_history_score(claims: ClaimsSummaryInput, ruleset: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    cfg = ruleset["components"]["claims_history"]

    count = max(0, claims.claim_count)
    if count == 0:
        freq_score = int(cfg["frequency"]["zero_claims_score"])
    elif count == 1:
        freq_score = int(cfg["frequency"]["one_claim_score"])
    elif count == 2:
        freq_score = int(cfg["frequency"]["two_claims_score"])
    else:
        freq_score = int(cfg["frequency"]["three_or_more_claims_score"])

    severity_amount = max(0.0, claims.total_paid_amount) + max(0.0, claims.total_reserved_amount)
    sev_cfg = cfg["severity"]
    if severity_amount <= float(sev_cfg["low_usd"]):
        sev_score = int(sev_cfg["low_score"])
    elif severity_amount <= float(sev_cfg["medium_usd"]):
        sev_score = int(sev_cfg["medium_score"])
    elif severity_amount <= float(sev_cfg["high_usd"]):
        sev_score = int(sev_cfg["high_score"])
    else:
        sev_score = int(sev_cfg["extreme_score"])

    blend = cfg["blend"]
    combined = (float(blend["frequency_weight"]) * freq_score) + (float(blend["severity_weight"]) * sev_score)
    score = _clamp_int(combined, 0, 100)

    details = {
        "claim_count": count,
        "severity_amount": severity_amount,
        "frequency_score": freq_score,
        "severity_score": sev_score,
        "lookback_months": int(claims.lookback_months),
        "blend": {"frequency_weight": float(blend["frequency_weight"]), "severity_weight": float(blend["severity_weight"])},
    }
    return score, details


def compute_telematics_behavior_score(telematics: Optional[TelematicsAggregateInput], ruleset: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    cfg = ruleset["components"]["telematics_behavior"]

    if telematics is None:
        # Deterministic missing-data posture: treat as moderate risk.
        return 50, {"missing": True, "default_score": 50}

    miles = max(0.0, telematics.miles_driven)
    per100 = _safe_div(100.0, miles) if miles > 0 else 0.0

    rates = {
        "harsh_braking": float(telematics.harsh_braking_events) * per100,
        "speeding": float(telematics.speeding_events) * per100,
        "distracted": float(telematics.distracted_driving_events) * per100,
        "night": float(telematics.night_driving_pct),
    }

    rate_cfg = cfg["event_rates_per_100_miles"]
    night_cfg = cfg["night_driving_pct"]

    sub_scores = {
        "harsh_braking": _tier_score(rates["harsh_braking"], rate_cfg["harsh_braking"]["low"], rate_cfg["harsh_braking"]["medium"], rate_cfg["harsh_braking"]["high"], 10, 45, 80, 100),
        "speeding": _tier_score(rates["speeding"], rate_cfg["speeding"]["low"], rate_cfg["speeding"]["medium"], rate_cfg["speeding"]["high"], 10, 50, 85, 100),
        "distracted": _tier_score(rates["distracted"], rate_cfg["distracted"]["low"], rate_cfg["distracted"]["medium"], rate_cfg["distracted"]["high"], 10, 55, 90, 100),
        "night": _tier_score(rates["night"], night_cfg["low"], night_cfg["medium"], night_cfg["high"], 10, 45, 75, 95),
    }

    w = cfg["sub_weights"]
    combined = (
        float(w["harsh_braking"]) * sub_scores["harsh_braking"]
        + float(w["speeding"]) * sub_scores["speeding"]
        + float(w["distracted"]) * sub_scores["distracted"]
        + float(w["night"]) * sub_scores["night"]
    )

    score = _clamp_int(combined, 0, 100)

    details = {
        "miles_driven": miles,
        "rates_per_100_miles": {k: rates[k] for k in ("harsh_braking", "speeding", "distracted")},
        "night_driving_pct": rates["night"],
        "sub_scores": sub_scores,
        "sub_weights": {k: float(w[k]) for k in w},
        "period_start": telematics.period_start.isoformat(),
        "period_end": telematics.period_end.isoformat(),
    }
    return score, details


def compute_iot_asset_health_score(iot: Optional[IoTAssetMetricInput], ruleset: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    cfg = ruleset["components"]["iot_asset_health"]

    if iot is None:
        return 50, {"missing": True, "default_score": 50}

    # Health score is inverted into risk score.
    hs = int(iot.health_score)
    health_cfg = cfg["health_score"]
    if hs >= int(health_cfg["good_min"]):
        health_risk = 10
    elif hs >= int(health_cfg["warning_min"]):
        health_risk = 45
    elif hs >= int(health_cfg["critical_min"]):
        health_risk = 75
    else:
        health_risk = 95

    anomalies = max(0, int(iot.anomaly_count))
    a_cfg = cfg["anomaly_count"]
    if anomalies <= int(a_cfg["low"]):
        anomaly_risk = 15
    elif anomalies <= int(a_cfg["medium"]):
        anomaly_risk = 55
    elif anomalies <= int(a_cfg["high"]):
        anomaly_risk = 85
    else:
        anomaly_risk = 100

    w = cfg["sub_weights"]
    combined = float(w["health"]) * health_risk + float(w["anomalies"]) * anomaly_risk
    score = _clamp_int(combined, 0, 100)

    details = {
        "captured_at": iot.captured_at.isoformat(),
        "device_id": iot.device_id,
        "health_score": hs,
        "anomaly_count": anomalies,
        "health_risk": health_risk,
        "anomaly_risk": anomaly_risk,
        "sub_weights": {k: float(w[k]) for k in w},
    }
    return score, details


def compute_climate_hazard_score(climate: Optional[ClimateIndexInput], ruleset: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    cfg = ruleset["components"]["climate_hazard"]

    if climate is None:
        default_idx = int(cfg["missing_hazard_index_default"])
        return default_idx, {"missing": True, "default_hazard_index": default_idx}

    hz = _clamp_int(float(climate.hazard_index), 0, 100)
    details = {
        "region_code": climate.region_code,
        "peril_type": climate.peril_type,
        "index_date": climate.index_date.isoformat(),
        "hazard_index": hz,
    }
    return hz, details


def compute_policy_exposure_score(policy: PolicyInput, ruleset: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    cfg = ruleset["components"]["policy_exposure"]

    asset_value = max(0.0, float(policy.asset_value))
    a_cfg = cfg["asset_value_usd"]
    asset_risk = _tier_score(asset_value, a_cfg["low"], a_cfg["medium"], a_cfg["high"], 10, 35, 60, 80)

    coverage_limit = max(0.0, float(policy.coverage_limit))
    deductible = max(0.0, float(policy.deductible))
    deductible_ratio = _safe_div(deductible, coverage_limit) if coverage_limit > 0 else 0.0

    d_cfg = cfg["deductible_ratio"]
    # Lower deductible_ratio => higher exposure risk.
    if deductible_ratio <= float(d_cfg["low"]):
        ded_risk = 75
    elif deductible_ratio <= float(d_cfg["medium"]):
        ded_risk = 45
    elif deductible_ratio <= float(d_cfg["high"]):
        ded_risk = 20
    else:
        ded_risk = 10

    w = cfg["sub_weights"]
    combined = float(w["asset_value"]) * asset_risk + float(w["deductible_ratio"]) * ded_risk
    score = _clamp_int(combined, 0, 100)

    details = {
        "asset_value": asset_value,
        "asset_risk": asset_risk,
        "coverage_limit": coverage_limit,
        "deductible": deductible,
        "deductible_ratio": deductible_ratio,
        "deductible_ratio_risk": ded_risk,
        "sub_weights": {k: float(w[k]) for k in w},
    }
    return score, details


def compute_components(inputs: RiskInputBundle, ruleset: Dict[str, Any]) -> List[RiskComponentResult]:
    weights = ruleset["weights"]

    results: List[RiskComponentResult] = []

    claims_score, claims_details = compute_claims_history_score(inputs.claims, ruleset)
    results.append(
        RiskComponentResult(
            component_name="claims_history",
            raw_value=None,
            normalized_score=claims_score,
            weight=float(weights["claims_history"]),
            weighted_score=float(weights["claims_history"]) * claims_score,
            details=claims_details,
        )
    )

    tele_score, tele_details = compute_telematics_behavior_score(inputs.telematics, ruleset)
    results.append(
        RiskComponentResult(
            component_name="telematics_behavior",
            raw_value=None,
            normalized_score=tele_score,
            weight=float(weights["telematics_behavior"]),
            weighted_score=float(weights["telematics_behavior"]) * tele_score,
            details=tele_details,
        )
    )

    iot_score, iot_details = compute_iot_asset_health_score(inputs.iot, ruleset)
    results.append(
        RiskComponentResult(
            component_name="iot_asset_health",
            raw_value=None,
            normalized_score=iot_score,
            weight=float(weights["iot_asset_health"]),
            weighted_score=float(weights["iot_asset_health"]) * iot_score,
            details=iot_details,
        )
    )

    climate_score, climate_details = compute_climate_hazard_score(inputs.climate, ruleset)
    results.append(
        RiskComponentResult(
            component_name="climate_hazard",
            raw_value=float(climate_score),
            normalized_score=climate_score,
            weight=float(weights["climate_hazard"]),
            weighted_score=float(weights["climate_hazard"]) * climate_score,
            details=climate_details,
        )
    )

    policy_score, policy_details = compute_policy_exposure_score(inputs.policy, ruleset)
    results.append(
        RiskComponentResult(
            component_name="policy_exposure",
            raw_value=None,
            normalized_score=policy_score,
            weight=float(weights["policy_exposure"]),
            weighted_score=float(weights["policy_exposure"]) * policy_score,
            details=policy_details,
        )
    )

    return results


def compute_lri(components: List[RiskComponentResult]) -> int:
    total_weight = sum(c.weight for c in components)
    # Deterministic guard: if weights don't sum to 1, normalize by total_weight.
    if total_weight <= 0:
        return 0

    weighted_sum = sum(c.weighted_score for c in components)
    normalized = weighted_sum / total_weight
    return _clamp_int(normalized, 0, 100)


def assign_band(lri: int, ruleset: Dict[str, Any]) -> str:
    score = _clamp_int(float(lri), 0, 100)
    for band in ruleset["risk_bands"]:
        if int(band["min"]) <= score <= int(band["max"]):
            return str(band["band"])
    return "MEDIUM"


def build_rule_context(inputs: RiskInputBundle, components: List[RiskComponentResult], lri: int, band: str) -> Dict[str, Any]:
    component_map = {c.component_name: asdict(c) for c in components}
    return {
        "risk": {"lri": lri, "band": band},
        "components": component_map,
        "inputs": {
            "policy": asdict(inputs.policy),
            "claims": asdict(inputs.claims),
            "telematics": asdict(inputs.telematics) if inputs.telematics else None,
            "iot": asdict(inputs.iot) if inputs.iot else None,
            "climate": asdict(inputs.climate) if inputs.climate else None,
        },
    }
