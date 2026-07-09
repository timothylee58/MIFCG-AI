from fastapi import APIRouter
from datetime import datetime, timezone

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "mifcg-api",
    }


@router.get("/health/ready")
async def readiness():
    """Checks connectivity to Supabase and Redis."""
    checks: dict[str, str] = {}

    try:
        from app.core.supabase import get_supabase
        sb = get_supabase()
        sb.table("profiles").select("id").limit(1).execute()
        checks["supabase"] = "ok"
    except Exception as exc:
        checks["supabase"] = f"error: {exc}"

    try:
        from app.core.redis import get_redis
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    try:
        import anthropic
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        anthropic.Anthropic(api_key=settings.anthropic_api_key)
        checks["anthropic"] = "ok"
    except Exception as exc:
        checks["anthropic"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}
