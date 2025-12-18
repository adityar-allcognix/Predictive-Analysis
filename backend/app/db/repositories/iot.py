from __future__ import annotations

from typing import Any, Dict, Optional

import asyncpg


async def get_latest_iot(conn: asyncpg.Connection, policy_id: str) -> Optional[Dict[str, Any]]:
    row = await conn.fetchrow(
        """
        SELECT captured_at, device_id, health_score::int, anomaly_count::int
        FROM iot_asset_metrics
        WHERE policy_id = $1::uuid
        ORDER BY captured_at DESC
        LIMIT 1
        """,
        policy_id,
    )
    return dict(row) if row else None
