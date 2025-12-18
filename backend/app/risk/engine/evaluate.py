from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .rule_eval import apply_rules
from .scoring import assign_band, build_rule_context, compute_components, compute_lri, load_ruleset
from .types import RiskEvaluationResult, RiskInputBundle


DEFAULT_RULESET_PATH = Path(__file__).resolve().parents[1] / "rules" / "ruleset_v1.json"


def evaluate_risk(inputs: RiskInputBundle, ruleset_path: Path = DEFAULT_RULESET_PATH) -> RiskEvaluationResult:
    ruleset = load_ruleset(ruleset_path)

    components = compute_components(inputs, ruleset)
    lri = compute_lri(components)
    band = assign_band(lri, ruleset)

    context = build_rule_context(inputs, components, lri, band)
    fired_rules, actions = apply_rules(ruleset, context)

    explanation: Dict[str, Any] = {
        "model": {"ruleset_name": ruleset.get("ruleset_name"), "version": ruleset.get("version")},
        "summary": {
            "loss_risk_index": lri,
            "risk_band": band,
            "component_scores": {c.component_name: c.normalized_score for c in components},
            "fired_rules": fired_rules,
        },
        "notes": [
            "Deterministic computation using explicit thresholds and weights.",
            "Missing signals use deterministic defaults as documented in the ruleset.",
        ],
    }

    return RiskEvaluationResult(
        loss_risk_index=lri,
        risk_band=band,
        components=components,
        fired_rules=fired_rules,
        preventive_actions=actions,
        explanation=explanation,
    )
