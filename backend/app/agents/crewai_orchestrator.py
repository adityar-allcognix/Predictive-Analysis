from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.agents.crewai_wrapper import crewai_available
from app.agents.orchestrator import DeterministicOrchestrator
from app.risk.engine.types import RiskEvaluationResult


class CrewAIOrchestrator:
    """CrewAI-compatible orchestrator (deterministic).

    Design goal:
    - Keep *all* decisions deterministic (ruleset + scoring).
    - Use CrewAI as an orchestration boundary only (agent/task naming, logging).

    Implementation note:
    - For strict determinism, this class intentionally does not rely on an LLM.
    - It mirrors the required three-agent flow by delegating to deterministic steps.
    """

    def __init__(self) -> None:
        self._det = DeterministicOrchestrator()

    async def run_with_conn(self, conn, policy_number: str) -> Tuple[Any, RiskEvaluationResult, Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
        if not crewai_available():
            # Fall back gracefully if dependency isn't present.
            return await self._det.run_with_conn(conn, policy_number)

        # Optional: construct CrewAI objects for metadata/consistency.
        # We do not call any LLM-backed kickoff to preserve determinism.
        try:
            from crewai import Agent, Task, Crew, Process  # noqa: F401

            _ = Agent(role="Data Aggregation Agent", goal="Aggregate deterministic inputs", backstory="Stateless deterministic", allow_delegation=False)
            _ = Agent(role="Risk Evaluation Agent", goal="Compute LRI deterministically", backstory="Stateless deterministic", allow_delegation=False)
            _ = Agent(role="Preventive Action Agent", goal="Apply rules deterministically", backstory="Stateless deterministic", allow_delegation=False)
            _ = Task(description="Aggregate inputs", expected_output="RiskInputBundle")
            _ = Task(description="Compute risk", expected_output="RiskEvaluationResult")
            _ = Task(description="Apply rules", expected_output="PreventiveActions")
            _ = Crew(agents=[], tasks=[], process=Process.sequential)
        except Exception:
            # If CrewAI API changes, determinism still holds; we just fall back to deterministic flow.
            pass

        return await self._det.run_with_conn(conn, policy_number)
