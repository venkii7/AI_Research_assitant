"""Per-plan rate limiting using slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.config import get_settings

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address, storage_uri=settings.upstash_redis_url
)

# Plan-based limits — applied per route
FREE_PROCESS_LIMIT = "5/month"  # paper processing
PRO_PROCESS_LIMIT = "200/day"
FREE_QUERY_LIMIT = "20/day"
PRO_QUERY_LIMIT = "500/day"
FREE_EXPORT_LIMIT = "0/day"  # exports blocked for free users
PRO_EXPORT_LIMIT = "50/day"
