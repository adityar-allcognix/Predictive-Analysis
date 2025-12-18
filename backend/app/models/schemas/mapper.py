from __future__ import annotations

import json
from typing import Any, Dict

from app.models.schemas.risk import RiskEvaluationResponse


def to_risk_evaluation_response(db_row: Dict[str, Any]) -> RiskEvaluationResponse:
    explanation: Any = db_row.get("explanation", {}) or {}
    if isinstance(explanation, str):
        try:
            explanation = json.loads(explanation)
        except json.JSONDecodeError:
            explanation = {}

    input_snapshot: Any = db_row.get("input_snapshot", {}) or {}
    if isinstance(input_snapshot, str):
        try:
            input_snapshot = json.loads(input_snapshot)
        except json.JSONDecodeError:
            input_snapshot = {}

    fired_rules = explanation.get("summary", {}).get("fired_rules", [])

    return RiskEvaluationResponse(
        risk_evaluation_id=db_row["risk_evaluation_id"],
        policy_id=db_row["policy_id"],
        policy_number=db_row.get("policy_number", ""),
        policy_type=db_row.get("policy_type", ""),
        evaluated_at=db_row["evaluated_at"],
        loss_risk_index=int(db_row["loss_risk_index"]),
        risk_band=str(db_row["risk_band"]),
        rule_version={
            "rule_version_id": db_row["rule_version_id"],
            "ruleset_name": db_row["ruleset_name"],
            "version": db_row["version"],
            "rules_sha256": db_row["rules_sha256"],
        },
        components=db_row["components"],
        fired_rules=fired_rules,
        preventive_actions=[
            {
                "rule_id": a.get("rule_id", ""),
                "action_type": a["action_type"],
                "priority": int(a["priority"]),
                "action_payload": a.get("action_payload", {}),
                "rationale": a.get("rationale", ""),
            }
            for a in db_row.get("preventive_actions", [])
        ],
        input_snapshot=input_snapshot,
        explanation=explanation,
    )
