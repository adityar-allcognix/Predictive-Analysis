from __future__ import annotations

from datetime import date
from typing import Any, Dict

import asyncpg


async def get_claims_summary(conn: asyncpg.Connection, policy_id: str, lookback_start: date) -> Dict[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT
          COUNT(*)::int AS claim_count,
          COALESCE(SUM(paid_amount), 0)::float8 AS total_paid_amount,
          COALESCE(SUM(reserve_amount), 0)::float8 AS total_reserved_amount
        FROM claims
        WHERE policy_id = $1::uuid
          AND loss_date >= $2::date
        """,
        policy_id,
        lookback_start,
    )
    return dict(row) if row else {"claim_count": 0, "total_paid_amount": 0.0, "total_reserved_amount": 0.0}
