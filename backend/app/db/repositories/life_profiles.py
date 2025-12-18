from __future__ import annotations

from typing import Any, Dict, Optional

import asyncpg


async def get_life_profile(conn: asyncpg.Connection, policy_id: str) -> Optional[Dict[str, Any]]:
    row = await conn.fetchrow(
        """
        SELECT policy_id::text, insured_age
        FROM life_policy_profiles
        WHERE policy_id = $1::uuid
        """,
        policy_id,
    )
    return dict(row) if row else None
