from __future__ import annotations

from typing import Any, Dict

import asyncpg


async def get_policy(
    conn: asyncpg.Connection,
    policy_id: str,
) -> Dict[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT policy_id::text, policy_number, policy_type, customer_id,
               insured_id, product_line, region_code, asset_type,
               asset_value::float8, coverage_limit::float8, deductible::float8,
               effective_date, expiry_date
        FROM policies
        WHERE policy_id = $1::uuid
        """,
        policy_id,
    )
    if row is None:
        raise KeyError(f"Policy not found: {policy_id}")
    return dict(row)


async def get_policy_by_number(
    conn: asyncpg.Connection,
    policy_number: str,
) -> Dict[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT policy_id::text, policy_number, policy_type, customer_id,
               insured_id, product_line, region_code, asset_type,
               asset_value::float8, coverage_limit::float8, deductible::float8,
               effective_date, expiry_date
        FROM policies
        WHERE policy_number = $1
        """,
        policy_number,
    )
    if row is None:
        raise KeyError(f"Policy not found: {policy_number}")
    return dict(row)
