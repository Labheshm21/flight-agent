import os
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase credentials. Add SUPABASE_URL and SUPABASE_KEY "
            "to .env, or use NEXT_PUBLIC_SUPABASE_URL and "
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY."
        )

    return create_client(url, key)


def list_flights(limit: int = 10) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    response = (
        supabase.table("flights")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


def insert_flight(
    flight_number: str,
    origin: str,
    destination: str,
    status: str = "scheduled",
) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    response = (
        supabase.table("flights")
        .insert(
            {
                "flight_number": flight_number,
                "origin": origin,
                "destination": destination,
                "status": status,
            }
        )
        .execute()
    )
    return response.data
