from __future__ import annotations

from dataclasses import dataclass

from app.risk.engine.types import PolicyInput


@dataclass(frozen=True)
class LifeProfileInput:
    insured_age: int


@dataclass(frozen=True)
class LifeRiskInputBundle:
    policy: PolicyInput
    profile: LifeProfileInput
    tenure_years: int
    mortality_index: int
