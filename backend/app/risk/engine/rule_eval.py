from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .types import PreventiveActionResult


class RuleEvaluationError(ValueError):
    pass


def _get_path(obj: Any, path: str) -> Any:
    # Supports dotted lookup into nested dicts: "a.b.c".
    current = obj
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _compare(op: str, actual: Any, expected: Any) -> bool:
    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    if op == "gt":
        return actual is not None and actual > expected
    if op == "gte":
        return actual is not None and actual >= expected
    if op == "lt":
        return actual is not None and actual < expected
    if op == "lte":
        return actual is not None and actual <= expected
    if op == "in":
        return actual in expected
    raise RuleEvaluationError(f"Unsupported operator: {op}")


def _eval_condition(
    condition: Dict[str, Any],
    context: Dict[str, Any],
) -> bool:
    path = condition.get("path")
    op = condition.get("op")
    expected = condition.get("value")
    if not path or not op:
        raise RuleEvaluationError("Condition requires 'path' and 'op'")
    actual = _get_path(context, str(path))
    return _compare(str(op), actual, expected)


def _eval_conditions(tree: Dict[str, Any], context: Dict[str, Any]) -> bool:
    if "all" in tree:
        conds = tree["all"]
        if not isinstance(conds, list):
            raise RuleEvaluationError("'all' must be a list")
        return all(_eval_condition(c, context) for c in conds)

    if "any" in tree:
        conds = tree["any"]
        if not isinstance(conds, list):
            raise RuleEvaluationError("'any' must be a list")
        return any(_eval_condition(c, context) for c in conds)

    # Single leaf condition fallback
    if "path" in tree and "op" in tree:
        return _eval_condition(tree, context)

    raise RuleEvaluationError("Invalid conditions tree")


def apply_rules(
    ruleset: Dict[str, Any],
    context: Dict[str, Any],
) -> Tuple[List[str], List[PreventiveActionResult]]:
    fired: List[str] = []
    actions: List[PreventiveActionResult] = []

    for rule in ruleset.get("rules", []):
        rule_id = str(rule.get("rule_id"))
        conditions = rule.get("conditions")
        if not conditions:
            continue

        if _eval_conditions(conditions, context):
            fired.append(rule_id)
            action = rule.get("action", {})
            actions.append(
                PreventiveActionResult(
                    rule_id=rule_id,
                    action_type=str(action.get("action_type")),
                    priority=int(action.get("priority", 3)),
                    action_payload=dict(action.get("action_payload", {})),
                    rationale=str(action.get("rationale", "")),
                )
            )

    # Deterministic ordering for auditability
    actions_sorted = sorted(
        actions,
        key=lambda a: (a.priority, a.action_type, a.rule_id),
    )
    fired_sorted = sorted(set(fired))
    return fired_sorted, actions_sorted
