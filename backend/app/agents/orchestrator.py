from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.db.repositories.policies import get_policy_by_number
from app.risk.engine.types import RiskEvaluationResult
from app.risk.engines.dispatcher import evaluate_by_policy_type, parse_policy_type_from_policy_number
from app.services.data_aggregation_service import aggregate_health_inputs, aggregate_inputs, aggregate_life_inputs


class DeterministicOrchestrator:
    """Deterministic orchestration that mirrors required CrewAI agents.

    This is the source of truth for decision logic. CrewAI integration (if enabled)
    must not alter decisions; it can only wrap and log these deterministic steps.
    """

    async def run_with_conn(self, conn, policy_number: str) -> Tuple[Any, RiskEvaluationResult, Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
        agent_events: List[Dict[str, Any]] = []

        policy_row = await get_policy_by_number(conn, policy_number)
        policy_id = policy_row["policy_id"]
        db_policy_type = str(policy_row.get("policy_type") or "").upper()
        parsed_policy_type = parse_policy_type_from_policy_number(policy_number)
        if db_policy_type and db_policy_type != parsed_policy_type:
            raise ValueError(f"Policy type mismatch for {policy_number}: DB has {db_policy_type} but prefix implies {parsed_policy_type}")
        policy_type = parsed_policy_type

        started = datetime.utcnow()
        try:
            if policy_type == "AUTO":
                inputs = await aggregate_inputs(conn, policy_id)
            elif policy_type == "HLTH":
                inputs = await aggregate_health_inputs(conn, policy_id)
            elif policy_type == "LIFE":
                inputs = await aggregate_life_inputs(conn, policy_id)
            else:
                raise ValueError(f"Unsupported policy_type: {policy_type}")
            finished = datetime.utcnow()
            agent_events.append(
                {
                    "risk_evaluation_id": None,
                    "policy_id": policy_id,
                    "agent_name": "DataAggregationAgent",
                    "task_name": "aggregate_inputs",
                    "status": "SUCCEEDED",
                    "started_at": started,
                    "finished_at": finished,
                    "input_payload": {"policy_number": policy_number, "policy_id": policy_id, "policy_type": policy_type},
                    "output_payload": {"aggregated": True, "policy_type": policy_type},
                    "error_message": None,
                }
            )
        except Exception as exc:
            finished = datetime.utcnow()
            agent_events.append(
                {
                    "risk_evaluation_id": None,
                    "policy_id": policy_id,
                    "agent_name": "DataAggregationAgent",
                    "task_name": "aggregate_inputs",
                    "status": "FAILED",
                    "started_at": started,
                    "finished_at": finished,
                    "input_payload": {"policy_number": policy_number, "policy_id": policy_id, "policy_type": policy_type},
                    "output_payload": {},
                    "error_message": str(exc),
                }
            )
            raise

        started2 = datetime.utcnow()
        try:
            evaluation, ruleset, ruleset_path = evaluate_by_policy_type(policy_type=policy_type, inputs=inputs)
            finished2 = datetime.utcnow()
            agent_events.append(
                {
                    "risk_evaluation_id": None,
                    "policy_id": policy_id,
                    "agent_name": "RiskEvaluationAgent",
                    "task_name": "compute_lri",
                    "status": "SUCCEEDED",
                    "started_at": started2,
                    "finished_at": finished2,
                    "input_payload": {"policy_number": policy_number, "policy_id": policy_id, "policy_type": policy_type},
                    "output_payload": {
                        "lri": evaluation.loss_risk_index,
                        "band": evaluation.risk_band,
                        "ruleset_name": ruleset.get("ruleset_name"),
                        "ruleset_version": ruleset.get("version"),
                        "ruleset_path": str(ruleset_path),
                    },
                    "error_message": None,
                }
            )

            started3 = datetime.utcnow()
            finished3 = datetime.utcnow()
            agent_events.append(
                {
                    "risk_evaluation_id": None,
                    "policy_id": policy_id,
                    "agent_name": "PreventiveActionAgent",
                    "task_name": "apply_rules",
                    "status": "SUCCEEDED",
                    "started_at": started3,
                    "finished_at": finished3,
                    "input_payload": {"policy_number": policy_number, "policy_id": policy_id, "policy_type": policy_type},
                    "output_payload": {"fired_rules": evaluation.fired_rules, "action_count": len(evaluation.preventive_actions)},
                    "error_message": None,
                }
            )
        except Exception as exc:
            finished2 = datetime.utcnow()
            agent_events.append(
                {
                    "risk_evaluation_id": None,
                    "policy_id": policy_id,
                    "agent_name": "RiskEvaluationAgent",
                    "task_name": "compute_lri",
                    "status": "FAILED",
                    "started_at": started2,
                    "finished_at": finished2,
                    "input_payload": {"policy_number": policy_number, "policy_id": policy_id, "policy_type": policy_type},
                    "output_payload": {},
                    "error_message": str(exc),
                }
            )
            raise

        # Type-specific snapshot for auditability.
        snapshot: Dict[str, Any] = {"policy_type": policy_type, "policy_number": policy_number, "policy_id": policy_id}
        if policy_type == "AUTO":
            snapshot.update(
                {
                    "policy": asdict(inputs.policy),
                    "claims": asdict(inputs.claims),
                    "telematics": asdict(inputs.telematics) if getattr(inputs, "telematics", None) else None,
                    "iot": asdict(inputs.iot) if getattr(inputs, "iot", None) else None,
                    "climate": asdict(inputs.climate) if getattr(inputs, "climate", None) else None,
                }
            )
        elif policy_type == "HLTH":
            snapshot.update({"policy": asdict(inputs.policy), "claims": asdict(inputs.claims), "profile": asdict(inputs.profile)})
        elif policy_type == "LIFE":
            snapshot.update(
                {
                    "policy": asdict(inputs.policy),
                    "profile": asdict(inputs.profile),
                    "tenure_years": int(inputs.tenure_years),
                    "mortality_index": int(inputs.mortality_index),
                }
            )

        return inputs, evaluation, snapshot, agent_events, {"policy_id": policy_id, "policy_type": policy_type, "policy_number": policy_number, "ruleset": ruleset}
