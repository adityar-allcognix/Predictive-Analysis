from __future__ import annotations

import json
from typing import Any, Dict, Optional

import asyncpg


async def get_health_profile(conn: asyncpg.Connection, policy_id: str) -> Optional[Dict[str, Any]]:
    row = await conn.fetchrow(
        """
        SELECT policy_id::text, member_age, chronic_flags
        FROM health_policy_profiles
        WHERE policy_id = $1::uuid
        """,
        policy_id,
    )
    if not row:
        return None

    data = dict(row)
    flags = data.get("chronic_flags")
    if isinstance(flags, str):
        try:
            data["chronic_flags"] = json.loads(flags)
        except json.JSONDecodeError:
            data["chronic_flags"] = {}
    return data
