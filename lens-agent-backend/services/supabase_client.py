"""Supabase client for all database operations."""
from supabase import create_client, Client
from core.config import get_settings
from datetime import datetime

settings = get_settings()
supabase: Client = create_client(
    settings.supabase_url, settings.supabase_service_role_key
)


# ── Papers ──────────────────────────────────────────────────────────────────


async def create_paper(user_id: str, data: dict) -> dict:
    """Create a new paper record."""
    result = supabase.table("papers").insert(
        {"user_id": user_id, "status": "queued", **data}
    ).execute()
    return result.data[0]


async def get_paper(paper_id: str, user_id: str) -> dict | None:
    """Get a single paper by ID (user must own it)."""
    result = (
        supabase.table("papers")
        .select("*")
        .eq("id", paper_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return result.data if result.data else None


async def list_papers(
    user_id: str, status: str | None, limit: int, offset: int
) -> list[dict]:
    """List papers for a user, optionally filtered by status."""
    query = supabase.table("papers").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    result = (
        query.order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data


async def update_paper(paper_id: str, data: dict) -> dict:
    """Update a paper record."""
    result = (
        supabase.table("papers")
        .update({**data, "updated_at": datetime.utcnow().isoformat()})
        .eq("id", paper_id)
        .execute()
    )
    return result.data[0] if result.data else {}


async def delete_paper(paper_id: str, user_id: str):
    """Soft delete a paper."""
    await update_paper(paper_id, {"status": "deleted"})


async def get_monthly_paper_count(user_id: str) -> int:
    """Count papers created this month for a user."""
    from datetime import date

    first_of_month = date.today().replace(day=1).isoformat()
    result = (
        supabase.table("papers")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .neq("status", "deleted")
        .gte("created_at", first_of_month)
        .execute()
    )
    return result.count or 0


# ── Users ───────────────────────────────────────────────────────────────────


async def get_user_plan(user_id: str) -> str:
    """Get the user's subscription plan."""
    result = (
        supabase.table("users")
        .select("plan")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return result.data.get("plan", "free") if result.data else "free"


async def get_or_create_user(auth_user: dict) -> dict:
    """Get or create a user record from Supabase Auth."""
    existing = (
        supabase.table("users")
        .select("*")
        .eq("supabase_auth_id", auth_user["id"])
        .execute()
    )
    if existing.data:
        return existing.data[0]
    result = supabase.table("users").insert(
        {
            "supabase_auth_id": auth_user["id"],
            "email": auth_user.get("email", ""),
            "plan": "free",
        }
    ).execute()
    return result.data[0]


# ── Exports ─────────────────────────────────────────────────────────────────


async def save_export(user_id: str, paper_id: str, format: str, content: str) -> dict:
    """Save an export to the database."""
    result = supabase.table("exports").insert(
        {
            "user_id": user_id,
            "paper_id": paper_id,
            "format": format,
            "output_text": content,
        }
    ).execute()
    return result.data[0] if result.data else {}
