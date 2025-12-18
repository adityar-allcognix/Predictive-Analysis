from __future__ import annotations

from typing import Optional

import asyncpg


async def get_mortality_index(conn: asyncpg.Connection, *, age: int) -> Optional[int]:
    row = await conn.fetchrow(
        """
        SELECT mortality_index
        FROM mortality_risk_table
        WHERE $1::int BETWEEN age_min AND age_max
        ORDER BY age_min ASC
        LIMIT 1
        """,
        age,
    )
    if not row:
        return None
    return int(row["mortality_index"])
