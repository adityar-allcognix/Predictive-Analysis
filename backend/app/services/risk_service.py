from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from app.db.pool import get_pool
from app.db.repositories.risk_persist import (
    ensure_rule_version,
    get_latest_evaluation_by_policy_number as db_get_latest_evaluation_by_policy_number,
    insert_actions,
    insert_components,
    insert_risk_evaluation,
)
from app.agents.orchestrator import DeterministicOrchestrator
from app.agents.crewai_orchestrator import CrewAIOrchestrator
from app.core.config import settings
from app.models.schemas.mapper import to_risk_evaluation_response
from app.models.schemas.risk import RiskEvaluationResponse


async def evaluate_policy_risk(policy_number: str) -> RiskEvaluationResponse:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            orchestrator = CrewAIOrchestrator() if settings.use_crewai else DeterministicOrchestrator()
            inputs, evaluation, snapshot, agent_events, meta = await orchestrator.run_with_conn(conn, policy_number)

            policy_id = meta["policy_id"]
            policy_type = meta["policy_type"]
            ruleset = meta["ruleset"]

            rule_version = await ensure_rule_version(conn, ruleset, created_by="system")

            risk_evaluation_id = await insert_risk_evaluation(
                conn,
                policy_id=policy_id,
                policy_number=policy_number,
                policy_type=policy_type,
                rule_version_id=rule_version["rule_version_id"],
                ruleset_name=str(rule_version["ruleset_name"]),
                ruleset_version=str(rule_version["version"]),
                rules_sha256=str(rule_version["rules_sha256"]),
                lri=evaluation.loss_risk_index,
                band=evaluation.risk_band,
                input_snapshot=snapshot,
                explanation=evaluation.explanation,
                evaluated_at=datetime.utcnow(),
            )

            component_dicts = [asdict(c) for c in evaluation.components]
            await insert_components(conn, risk_evaluation_id, component_dicts)

            action_dicts = [asdict(a) for a in evaluation.preventive_actions]
            await insert_actions(conn, risk_evaluation_id, action_dicts)

            # Persist agent logs linked to this evaluation for auditability.
            for ev in agent_events:
                ev = {**ev, "risk_evaluation_id": risk_evaluation_id}
                from app.db.repositories.risk_persist import insert_agent_log

                await insert_agent_log(conn, **ev)

        # Return full hydrated latest evaluation (includes persisted IDs)
        db_row = await db_get_latest_evaluation_by_policy_number(conn, policy_number)
        return to_risk_evaluation_response(db_row)


async def get_latest_evaluation(policy_number: str) -> RiskEvaluationResponse:
    pool = await get_pool()
    async with pool.acquire() as conn:
        db_row = await db_get_latest_evaluation_by_policy_number(conn, policy_number)
        return to_risk_evaluation_response(db_row)
