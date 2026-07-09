import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.core.auth import get_current_user, require_admin
from app.core.limiter import limiter
from app.core.redis import get_redis
from app.services.fxwatch import (
    BNMError,
    fetch_myr_rate,
    get_cached_rate,
    get_threshold_pct,
    set_threshold_pct,
)
from app.services.fxwatch.poller import PAIRS

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/fxwatch",
    tags=["fxwatch"],
    dependencies=[Depends(get_current_user)],
)

MYR_PAIRS = [f"MYR/{c}" for c in PAIRS]


class FXAlertConfig(BaseModel):
    pair: str = Field(..., description="ISO 4217 currency code, e.g. 'USD' or 'SGD'")
    threshold_pct: float = Field(..., gt=0, le=100)


@router.get("/")
async def fxwatch_info():
    return {
        "module": "FXWatch",
        "status": "active",
        "pairs": MYR_PAIRS,
        "poll_source": "BNM Open API",
        "endpoints": ["/rates", "/stream", "/alerts"],
    }


@router.get("/rates")
@limiter.limit("20/minute")
async def get_rates(request: Request):
    """Return the latest cached BNM rate for each monitored MYR corridor."""
    results = []
    for currency in PAIRS:
        snapshot = await get_cached_rate(currency)
        if snapshot is None:
            # Cache not yet populated (e.g. right after a cold start) — fetch live.
            try:
                rate = await fetch_myr_rate(currency)
                snapshot = {
                    "pair": f"MYR/{currency}",
                    "rate": rate.middle_rate,
                    "buying_rate": rate.buying_rate,
                    "selling_rate": rate.selling_rate,
                    "rate_date": rate.rate_date,
                    "session": rate.session,
                    "fetched_at": None,
                }
            except BNMError as exc:
                logger.error("Live fallback fetch failed for %s: %s", currency, exc)
                continue
        results.append(snapshot)
    return {"rates": results}


@router.get("/stream")
async def stream_rates(request: Request):
    """SSE-stream live FX ticks as the poller publishes new rates to Redis."""

    async def event_stream():
        redis = await get_redis()
        pubsub = redis.pubsub()
        channels = [f"fxwatch:updates:{c}" for c in PAIRS]
        await pubsub.subscribe(*channels)
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=15.0
                )
                if message is None:
                    yield {"event": "ping", "data": ""}
                    continue
                yield {"data": message["data"]}
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.close()

    return EventSourceResponse(event_stream())


@router.get("/alerts")
async def list_alert_thresholds():
    """Current per-pair alert thresholds (falls back to the default when unset)."""
    return {
        "thresholds": [
            {"pair": f"MYR/{c}", "threshold_pct": await get_threshold_pct(c)} for c in PAIRS
        ]
    }


@router.post("/alerts", dependencies=[Depends(require_admin)])
@limiter.limit("20/minute")
async def create_alert(request: Request, alert: FXAlertConfig):
    """Configure the corridor-breach alert threshold for a pair. Admin-only."""
    currency = alert.pair.upper().split("/")[-1]  # accept "USD" or "MYR/USD"
    if currency not in PAIRS:
        raise HTTPException(
            status_code=422, detail=f"Pair must be one of {[f'MYR/{c}' for c in PAIRS]}"
        )
    await set_threshold_pct(currency, alert.threshold_pct)
    return {"pair": f"MYR/{currency}", "threshold_pct": alert.threshold_pct}
