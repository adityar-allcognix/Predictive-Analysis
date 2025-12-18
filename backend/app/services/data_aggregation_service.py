from __future__ import annotations

from dataclasses import asdict
from datetime import date
from dateutil.relativedelta import relativedelta

import asyncpg

from app.db.repositories.claims import get_claims_summary
from app.db.repositories.climate import get_latest_climate_index
from app.db.repositories.health_profiles import get_health_profile
from app.db.repositories.iot import get_latest_iot
from app.db.repositories.life_profiles import get_life_profile
from app.db.repositories.mortality import get_mortality_index
from app.db.repositories.policies import get_policy
from app.db.repositories.telematics import get_latest_telematics
from app.risk.engine.types import (
    ClimateIndexInput,
    ClaimsSummaryInput,
    IoTAssetMetricInput,
    PolicyInput,
    RiskInputBundle,
    TelematicsAggregateInput,
)
from app.risk.engines.health_types import HealthProfileInput, HealthRiskInputBundle
from app.risk.engines.life_types import LifeProfileInput, LifeRiskInputBundle
from app.services.simulators import simulate_iot, simulate_telematics


def _stable_int(seed: str, *, min_v: int, max_v: int) -> int:
    import hashlib

    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    n = int(h[:8], 16)
    span = max(1, (max_v - min_v + 1))
    return min_v + (n % span)


async def aggregate_inputs(conn: asyncpg.Connection, policy_id: str) -> RiskInputBundle:
    policy_row = await get_policy(conn, policy_id)

    policy = PolicyInput(
        policy_id=policy_row["policy_id"],
        policy_number=policy_row["policy_number"],
        insured_id=policy_row["insured_id"],
        product_line=policy_row["product_line"],
        region_code=policy_row["region_code"],
        asset_type=policy_row["asset_type"],
        asset_value=float(policy_row["asset_value"]),
        coverage_limit=float(policy_row["coverage_limit"]),
        deductible=float(policy_row["deductible"]),
        effective_date=policy_row["effective_date"],
        expiry_date=policy_row["expiry_date"],
    )

    lookback_months = 36
    lookback_start = date.today() - relativedelta(months=lookback_months)
    claims_row = await get_claims_summary(conn, policy_id, lookback_start)
    claims = ClaimsSummaryInput(
        lookback_months=lookback_months,
        claim_count=int(claims_row["claim_count"]),
        total_paid_amount=float(claims_row["total_paid_amount"]),
        total_reserved_amount=float(claims_row["total_reserved_amount"]),
    )

    tele_row = await get_latest_telematics(conn, policy_id)
    if tele_row:
        telematics = TelematicsAggregateInput(**tele_row)
    else:
        # Deterministic simulation for demo/testing when telematics is not available.
        telematics = simulate_telematics(policy.policy_id)

    iot_row = await get_latest_iot(conn, policy_id)
    if iot_row:
        iot = IoTAssetMetricInput(**iot_row)
    else:
        iot = simulate_iot(policy.policy_id)

    # Climate: pick a stable default peril type for the MVP.
    peril_type = "flood"
    climate_row = await get_latest_climate_index(conn, policy.region_code, peril_type, date.today())
    climate = ClimateIndexInput(**climate_row) if climate_row else None

    return RiskInputBundle(policy=policy, claims=claims, telematics=telematics, iot=iot, climate=climate)


async def aggregate_health_inputs(conn: asyncpg.Connection, policy_id: str) -> HealthRiskInputBundle:
    policy_row = await get_policy(conn, policy_id)

    policy = PolicyInput(
        policy_id=policy_row["policy_id"],
        policy_number=policy_row["policy_number"],
        insured_id=policy_row["insured_id"],
        product_line=policy_row["product_line"],
        region_code=policy_row["region_code"],
        asset_type=policy_row["asset_type"],
        asset_value=float(policy_row["asset_value"]),
        coverage_limit=float(policy_row["coverage_limit"]),
        deductible=float(policy_row["deductible"]),
        effective_date=policy_row["effective_date"],
        expiry_date=policy_row["expiry_date"],
    )

    lookback_months = 36
    lookback_start = date.today() - relativedelta(months=lookback_months)
    claims_row = await get_claims_summary(conn, policy_id, lookback_start)
    claims = ClaimsSummaryInput(
        lookback_months=lookback_months,
        claim_count=int(claims_row["claim_count"]),
        total_paid_amount=float(claims_row["total_paid_amount"]),
        total_reserved_amount=float(claims_row["total_reserved_amount"]),
    )

    profile_row = await get_health_profile(conn, policy_id)
    if profile_row:
        profile = HealthProfileInput(member_age=int(profile_row["member_age"]), chronic_flags=profile_row.get("chronic_flags") or {})
    else:
        # Deterministic fallback for demo environments without a profile row.
        age = _stable_int(f"hlth-age:{policy_id}", min_v=25, max_v=70)
        profile = HealthProfileInput(member_age=age, chronic_flags={})

    return HealthRiskInputBundle(policy=policy, claims=claims, profile=profile)


async def aggregate_life_inputs(conn: asyncpg.Connection, policy_id: str) -> LifeRiskInputBundle:
    policy_row = await get_policy(conn, policy_id)

    policy = PolicyInput(
        policy_id=policy_row["policy_id"],
        policy_number=policy_row["policy_number"],
        insured_id=policy_row["insured_id"],
        product_line=policy_row["product_line"],
        region_code=policy_row["region_code"],
        asset_type=policy_row["asset_type"],
        asset_value=float(policy_row["asset_value"]),
        coverage_limit=float(policy_row["coverage_limit"]),
        deductible=float(policy_row["deductible"]),
        effective_date=policy_row["effective_date"],
        expiry_date=policy_row["expiry_date"],
    )

    profile_row = await get_life_profile(conn, policy_id)
    if profile_row:
        insured_age = int(profile_row["insured_age"])
    else:
        insured_age = _stable_int(f"life-age:{policy_id}", min_v=25, max_v=75)

    profile = LifeProfileInput(insured_age=insured_age)

    tenure_years = max(0, int((date.today() - policy.effective_date).days // 365))
    mortality_index = await get_mortality_index(conn, age=insured_age)
    if mortality_index is None:
        mortality_index = 50

    return LifeRiskInputBundle(policy=policy, profile=profile, tenure_years=tenure_years, mortality_index=int(mortality_index))
