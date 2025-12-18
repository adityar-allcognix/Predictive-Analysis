from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from app.risk.engine.types import ClaimsSummaryInput, PolicyInput


@dataclass(frozen=True)
class HealthProfileInput:
    member_age: int
    chronic_flags: Dict[str, Any]


@dataclass(frozen=True)
class HealthRiskInputBundle:
    policy: PolicyInput
    claims: ClaimsSummaryInput
    profile: HealthProfileInput
