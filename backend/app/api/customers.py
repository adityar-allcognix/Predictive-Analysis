from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.db.pool import get_pool

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/verify-email/{email}")
async def verify_customer_email(email: str):
    """
    Verify if a customer exists with the given email address.
    Returns customer details if found.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT customer_id, full_name, email, phone_number
                FROM customers
                WHERE email = $1
                """,
                email
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="No customer found with this email")
            
            return {
                "customer_id": row["customer_id"],
                "full_name": row["full_name"],
                "email": row["email"],
                "phone_number": row["phone_number"]
            }
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("Error verifying customer email")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/{customer_id}")
async def get_customer(customer_id: str):
    """
    Get customer details by customer ID.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT customer_id, full_name, email, phone_number
                FROM customers
                WHERE customer_id = $1
                """,
                customer_id
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            return {
                "customer_id": row["customer_id"],
                "full_name": row["full_name"],
                "email": row["email"],
                "phone_number": row["phone_number"]
            }
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("Error getting customer")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
