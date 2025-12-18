from __future__ import annotations

from typing import Any, Dict, Optional

import asyncpg


async def get_latest_telematics(conn: asyncpg.Connection, policy_id: str) -> Optional[Dict[str, Any]]:
    row = await conn.fetchrow(
        """
        SELECT period_start, period_end,
               miles_driven::float8, harsh_braking_events::int, speeding_events::int,
               distracted_driving_events::int, night_driving_pct::float8
        FROM telematics_aggregates
        WHERE policy_id = $1::uuid
        ORDER BY period_end DESC
        LIMIT 1
        """,
        policy_id,
    )
    return dict(row) if row else None
