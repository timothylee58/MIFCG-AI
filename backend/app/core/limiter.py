"""
Shared slowapi Limiter instance, backed by Redis so limits are shared
across all instances/workers rather than tracked in-process.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    # If Redis is briefly unavailable, fall back to an in-process memory
    # store so requests keep working (rate limits just stop being shared
    # across instances until Redis recovers) instead of raising errors.
    in_memory_fallback_enabled=True,
    # Belt-and-braces: never let a rate-limiter failure take the API down.
    swallow_errors=True,
)
