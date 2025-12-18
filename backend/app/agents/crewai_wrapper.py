from __future__ import annotations

from typing import Optional


def crewai_available() -> bool:
    try:
        import crewai  # noqa: F401

        return True
    except Exception:
        return False


def get_crewai_note() -> str:
    """Explains the CrewAI posture for determinism.

    This project keeps *all decisions* deterministic in Python (ruleset + scoring).
    CrewAI is used for orchestration/structure only and must not influence scoring.
    """

    if not crewai_available():
        return "CrewAI not installed; using deterministic in-process orchestrator."
    return "CrewAI installed; orchestrator can be wired to CrewAI without affecting decisions."
