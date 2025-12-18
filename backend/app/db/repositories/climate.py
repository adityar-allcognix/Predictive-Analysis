from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

import asyncpg


async def get_latest_climate_index(conn: asyncpg.Connection, region_code: str, peril_type: str, as_of: date) -> Optional[Dict[str, Any]]:
    row = await conn.fetchrow(
        """
        SELECT region_code, peril_type, index_date, hazard_index::int
        FROM climate_risk_indices
        WHERE region_code = $1
          AND peril_type = $2
          AND index_date <= $3::date
        ORDER BY index_date DESC
        LIMIT 1
        """,
        region_code,
        peril_type,
        as_of,
    )
    return dict(row) if row else None
