"""
Authentication and authorization dependencies.

All non-health routers require a valid Supabase JWT (``get_current_user``).
Admin-only routes additionally require ``require_admin``, which checks the
caller's role in the ``profiles`` table.

Note: ``get_supabase()`` uses the service-role key and therefore bypasses
Row Level Security entirely — these dependencies are what actually enforce
access control at the API layer.
"""

import logging
from typing import Any

from fastapi import Depends, Header, HTTPException

from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)


async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    """
    Validate the ``Authorization: Bearer <jwt>`` header against Supabase Auth.

    Returns a dict with at least ``id`` for use by downstream dependencies
    and route handlers.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        sb = get_supabase()
        response = sb.auth.get_user(token)
        user = getattr(response, "user", None)
        if user is None:
            raise ValueError("No user returned for token")
    except Exception as exc:
        logger.warning("Token validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    return {
        "id": user.id,
        "email": getattr(user, "email", None),
    }


async def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Require that the authenticated user has the 'admin' role in `profiles`."""
    try:
        sb = get_supabase()
        result = (
            sb.table("profiles")
            .select("role")
            .eq("id", user["id"])
            .limit(1)
            .execute()
        )
        rows = result.data or []
        role = rows[0]["role"] if rows else None
    except Exception as exc:
        logger.warning("Admin role lookup failed: %s", exc)
        raise HTTPException(status_code=403, detail="Admin access required") from exc

    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user
