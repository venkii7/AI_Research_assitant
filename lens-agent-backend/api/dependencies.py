"""Shared FastAPI dependencies for all routes."""
from fastapi import Depends, HTTPException
from core.security import get_current_user
from services.supabase_client import (
    get_or_create_user,
    get_user_plan,
    get_monthly_paper_count,
)
from core.config import get_settings

settings = get_settings()


async def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """Base auth dependency — verifies JWT and returns user dict."""
    return user


async def require_user_record(auth_user: dict = Depends(require_auth)) -> dict:
    """Ensures the user exists in the users table. Creates if first visit."""
    db_user = await get_or_create_user(auth_user)
    return {**auth_user, **db_user}


async def require_pro(user: dict = Depends(require_user_record)) -> dict:
    """Raise 403 if user is not on Pro plan."""
    if user.get("plan") not in ("pro", "team"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "This feature requires a Pro plan",
                "code": "plan_limit_reached",
                "details": {"current_plan": user.get("plan"), "required_plan": "pro"},
            },
        )
    return user


async def check_paper_limit(user: dict = Depends(require_user_record)):
    """
    For free users: check they haven't exceeded monthly paper limit.
    Pro users pass through with no check.
    """
    if user.get("plan") == "free":
        count = await get_monthly_paper_count(user["id"])
        limit = settings.max_free_papers_per_month
        if count >= limit:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": f"Free plan limit reached ({limit} papers/month)",
                    "code": "plan_limit_reached",
                    "details": {
                        "used": count,
                        "limit": limit,
                        "plan": "free",
                    },
                },
            )
    return user
