from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from typing import Tuple

from app.risk.engine.types import IoTAssetMetricInput, TelematicsAggregateInput


def _u64_from_sha256(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def _map_range(u64: int, low: float, high: float) -> float:
    if high <= low:
        return low
    # Deterministic mapping into [low, high]
    return low + (u64 % 10_000_000) / 10_000_000 * (high - low)


def simulate_telematics(policy_key: str, today: date | None = None) -> TelematicsAggregateInput:
    today = today or date.today()
    period_end = today
    period_start = today - timedelta(days=30)

    base = _u64_from_sha256(f"tele|{policy_key}")
    miles = _map_range(base, 250.0, 1800.0)

    # Event counts are deterministic and scale with miles.
    harsh = int(_map_range(_u64_from_sha256(f"hb|{policy_key}"), 0, max(1.0, miles / 120)))
    speeding = int(_map_range(_u64_from_sha256(f"sp|{policy_key}"), 0, max(2.0, miles / 90)))
    distracted = int(_map_range(_u64_from_sha256(f"dd|{policy_key}"), 0, max(1.0, miles / 160)))
    night_pct = float(_map_range(_u64_from_sha256(f"ng|{policy_key}"), 2.0, 45.0))

    return TelematicsAggregateInput(
        period_start=period_start,
        period_end=period_end,
        miles_driven=round(miles, 2),
        harsh_braking_events=harsh,
        speeding_events=speeding,
        distracted_driving_events=distracted,
        night_driving_pct=round(night_pct, 2),
    )


def simulate_iot(policy_key: str, now: datetime | None = None) -> IoTAssetMetricInput:
    now = now or datetime.utcnow()
    base = _u64_from_sha256(f"iot|{policy_key}")

    health = int(_map_range(base, 35, 95))
    anomalies = int(_map_range(_u64_from_sha256(f"an|{policy_key}"), 0, 8))

    device_id = f"SIM-{policy_key[:8]}"
    return IoTAssetMetricInput(captured_at=now, device_id=device_id, health_score=health, anomaly_count=anomalies)
