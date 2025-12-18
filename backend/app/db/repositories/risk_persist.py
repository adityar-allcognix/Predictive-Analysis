from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import asyncpg


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, default=_json_default)


def _json_loads_if_str(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


async def ensure_rule_version(conn: asyncpg.Connection, ruleset: Dict[str, Any], created_by: str = "system") -> Dict[str, Any]:
    ruleset_name = str(ruleset.get("ruleset_name"))
    version = str(ruleset.get("version"))
    rules_doc = ruleset

    payload = json.dumps(rules_doc, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")
    rules_sha256 = hashlib.sha256(payload).hexdigest()

    row = await conn.fetchrow(
        """
        SELECT rule_version_id::text, ruleset_name, version, rules_sha256
        FROM rule_versions
        WHERE ruleset_name = $1 AND rules_sha256 = $2
        """,
        ruleset_name,
        rules_sha256,
    )
    if row:
        return dict(row)

    inserted = await conn.fetchrow(
        """
        INSERT INTO rule_versions (ruleset_name, version, rules_sha256, rules_document, created_by)
        VALUES ($1, $2, $3, $4::jsonb, $5)
        RETURNING rule_version_id::text, ruleset_name, version, rules_sha256
        """,
        ruleset_name,
        version,
        rules_sha256,
        _json_dumps(rules_doc),
        created_by,
    )
    return dict(inserted)


async def insert_risk_evaluation(
    conn: asyncpg.Connection,
    policy_id: str,
    policy_number: str,
    policy_type: str,
    rule_version_id: str,
    ruleset_name: str,
    ruleset_version: str,
    rules_sha256: str,
    lri: int,
    band: str,
    input_snapshot: Dict[str, Any],
    explanation: Dict[str, Any],
    evaluated_at: datetime | None = None,
) -> str:
    evaluated_at = evaluated_at or datetime.utcnow()
    row = await conn.fetchrow(
        """
        INSERT INTO risk_evaluations (
          policy_id, policy_number, policy_type,
          evaluated_at, loss_risk_index, risk_band,
          rule_version_id, ruleset_name, ruleset_version, rules_sha256,
          input_snapshot, explanation
        )
        VALUES (
          $1::uuid, $2, $3,
          $4::timestamptz, $5::int, $6,
          $7::uuid, $8, $9, $10,
          $11::jsonb, $12::jsonb
        )
        RETURNING risk_evaluation_id::text
        """,
        policy_id,
        policy_number,
        policy_type,
        evaluated_at,
        lri,
        band,
        rule_version_id,
        ruleset_name,
        ruleset_version,
        rules_sha256,
        _json_dumps(input_snapshot),
        _json_dumps(explanation),
    )
    return str(row["risk_evaluation_id"])


async def get_latest_evaluation_by_policy_number(conn: asyncpg.Connection, policy_number: str) -> Dict[str, Any]:
    eval_row = await conn.fetchrow(
        """
        SELECT re.risk_evaluation_id::text, re.policy_id::text, re.policy_number, re.policy_type, re.evaluated_at,
               re.loss_risk_index, re.risk_band,
               rv.rule_version_id::text AS rule_version_id, rv.ruleset_name, rv.version, rv.rules_sha256,
               re.input_snapshot, re.explanation
        FROM risk_evaluations re
        JOIN rule_versions rv ON rv.rule_version_id = re.rule_version_id
        WHERE re.policy_number = $1
        ORDER BY re.evaluated_at DESC
        LIMIT 1
        """,
        policy_number,
    )
    if eval_row is None:
        raise KeyError(f"No evaluations found for policy: {policy_number}")

    components = await conn.fetch(
        """
        SELECT component_name, raw_value::float8, normalized_score, weight::float8, weighted_score::float8, details
        FROM risk_components
        WHERE risk_evaluation_id = $1::uuid
        ORDER BY component_name
        """,
        eval_row["risk_evaluation_id"],
    )

    actions = await conn.fetch(
        """
        SELECT rule_id, action_type, action_payload, priority, rationale
        FROM preventive_actions
        WHERE risk_evaluation_id = $1::uuid
        ORDER BY priority ASC, action_type ASC, rule_id ASC
        """,
        eval_row["risk_evaluation_id"],
    )

    base = dict(eval_row)
    base["input_snapshot"] = _json_loads_if_str(base.get("input_snapshot"))
    base["explanation"] = _json_loads_if_str(base.get("explanation"))

    component_dicts: List[Dict[str, Any]] = []
    for r in components:
        d = dict(r)
        d["details"] = _json_loads_if_str(d.get("details"))
        component_dicts.append(d)

    action_dicts: List[Dict[str, Any]] = []
    for r in actions:
        d = dict(r)
        d["action_payload"] = _json_loads_if_str(d.get("action_payload"))
        action_dicts.append(d)

    return {
        **base,
        "components": component_dicts,
        "preventive_actions": action_dicts,
    }


async def insert_components(conn: asyncpg.Connection, risk_evaluation_id: str, components: List[Dict[str, Any]]) -> None:
    for c in components:
        await conn.execute(
            """
            INSERT INTO risk_components (risk_evaluation_id, component_name, raw_value, normalized_score, weight, weighted_score, details)
            VALUES ($1::uuid, $2, $3::float8, $4::int, $5::float8, $6::float8, $7::jsonb)
            """,
            risk_evaluation_id,
            c["component_name"],
            c.get("raw_value"),
            int(c["normalized_score"]),
            float(c["weight"]),
            float(c["weighted_score"]),
            _json_dumps(c.get("details", {})),
        )


async def insert_actions(conn: asyncpg.Connection, risk_evaluation_id: str, actions: List[Dict[str, Any]]) -> None:
    for a in actions:
        await conn.execute(
            """
            INSERT INTO preventive_actions (risk_evaluation_id, rule_id, action_type, action_payload, priority, rationale)
            VALUES ($1::uuid, $2, $3, $4::jsonb, $5::int, $6)
            """,
            risk_evaluation_id,
            a.get("rule_id", ""),
            a["action_type"],
            _json_dumps(a.get("action_payload", {})),
            int(a.get("priority", 3)),
            a.get("rationale", ""),
        )


async def insert_agent_log(
    conn: asyncpg.Connection,
    *,
    risk_evaluation_id: str | None,
    policy_id: str | None,
    agent_name: str,
    task_name: str,
    status: str,
    started_at: datetime,
    finished_at: datetime | None,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    error_message: str | None = None,
) -> None:
    await conn.execute(
        """
        INSERT INTO agent_logs (
          risk_evaluation_id, policy_id, agent_name, task_name, status, started_at, finished_at,
          input_payload, output_payload, error_message
        )
        VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::timestamptz, $7::timestamptz, $8::jsonb, $9::jsonb, $10)
        """,
        risk_evaluation_id,
        policy_id,
        agent_name,
        task_name,
        status,
        started_at,
        finished_at,
        _json_dumps(input_payload),
        _json_dumps(output_payload),
        error_message,
    )


async def get_latest_evaluation(conn: asyncpg.Connection, policy_id: str) -> Dict[str, Any]:
    eval_row = await conn.fetchrow(
        """
        SELECT re.risk_evaluation_id::text, re.policy_id::text, re.evaluated_at,
               re.loss_risk_index, re.risk_band,
               rv.rule_version_id::text AS rule_version_id, rv.ruleset_name, rv.version, rv.rules_sha256,
               re.input_snapshot, re.explanation
        FROM risk_evaluations re
        JOIN rule_versions rv ON rv.rule_version_id = re.rule_version_id
        WHERE re.policy_id = $1::uuid
        ORDER BY re.evaluated_at DESC
        LIMIT 1
        """,
        policy_id,
    )
    if eval_row is None:
        raise KeyError(f"No evaluations found for policy: {policy_id}")

    components = await conn.fetch(
        """
        SELECT component_name, raw_value::float8, normalized_score, weight::float8, weighted_score::float8, details
        FROM risk_components
        WHERE risk_evaluation_id = $1::uuid
        ORDER BY component_name
        """,
        eval_row["risk_evaluation_id"],
    )

    actions = await conn.fetch(
        """
        SELECT rule_id, action_type, action_payload, priority, rationale
        FROM preventive_actions
        WHERE risk_evaluation_id = $1::uuid
        ORDER BY priority ASC, action_type ASC, rule_id ASC
        """,
        eval_row["risk_evaluation_id"],
    )

    base = dict(eval_row)
    base["input_snapshot"] = _json_loads_if_str(base.get("input_snapshot"))
    base["explanation"] = _json_loads_if_str(base.get("explanation"))

    component_dicts: List[Dict[str, Any]] = []
    for r in components:
        d = dict(r)
        d["details"] = _json_loads_if_str(d.get("details"))
        component_dicts.append(d)

    action_dicts: List[Dict[str, Any]] = []
    for r in actions:
        d = dict(r)
        d["action_payload"] = _json_loads_if_str(d.get("action_payload"))
        action_dicts.append(d)

    return {
        **base,
        "components": component_dicts,
        "preventive_actions": action_dicts,
    }
