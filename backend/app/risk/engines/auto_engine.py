from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from app.risk.engine.evaluate import evaluate_risk
from app.risk.engine.scoring import load_ruleset
from app.risk.engine.types import RiskEvaluationResult, RiskInputBundle


AUTO_RULESET_PATH = Path(__file__).resolve().parents[1] / "rules" / "auto_ruleset_v1.json"


def evaluate_auto(inputs: RiskInputBundle) -> Tuple[RiskEvaluationResult, Dict[str, Any]]:
    ruleset = load_ruleset(AUTO_RULESET_PATH)
    evaluation = evaluate_risk(inputs, ruleset_path=AUTO_RULESET_PATH)

    # Make type explicit in explainability.
    evaluation.explanation.setdefault("policy", {})
    evaluation.explanation["policy"].update({"policy_type": "AUTO", "policy_number": inputs.policy.policy_number})
    return evaluation, ruleset
