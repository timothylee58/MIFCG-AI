"""
Polling job: fetch BNM rates for the MYR/USD and MYR/SGD corridors every
few minutes, compare against the previously cached rate, and fire a Claude
Haiku narrative alert to Slack + Telegram on a threshold breach.

Runs inside the existing FastAPI process via APScheduler (see
app/services/fxwatch/scheduler.py) rather than a separate serverless
worker, backed by Redis instead of Cloudflare KV for rate caching.
"""

import json
import logging
import time

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.redis import get_redis
from .bnm_client import BNMError, fetch_myr_rate
from .narrator import generate_breach_narrative
from .notifiers import deliver_alert

logger = logging.getLogger(__name__)

PAIRS = ["USD", "SGD"]  # MYR/USD and MYR/SGD corridors
RATE_CACHE_PREFIX = "fxwatch:rate:"
THRESHOLD_PREFIX = "fxwatch:threshold:"
LOCK_KEY = "fxwatch:poll-lock"
LOCK_TTL_SECONDS = 240  # < the poll interval, so a crashed instance can't wedge the lock


async def get_threshold_pct(currency: str) -> float:
    """Per-pair configurable alert threshold, falling back to the default."""
    redis = await get_redis()
    raw = await redis.get(f"{THRESHOLD_PREFIX}{currency}")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return settings.fx_alert_threshold_pct


async def set_threshold_pct(currency: str, threshold_pct: float) -> None:
    redis = await get_redis()
    await redis.set(f"{THRESHOLD_PREFIX}{currency}", str(threshold_pct))


async def get_cached_rate(currency: str) -> dict | None:
    redis = await get_redis()
    raw = await redis.get(f"{RATE_CACHE_PREFIX}{currency}")
    return json.loads(raw) if raw else None


async def poll_once() -> None:
    """Single poll tick: fetch, compare, cache, and alert on breach for every pair."""
    redis = await get_redis()

    # Distributed lock so only one instance/worker runs a given tick even if
    # the backend is ever scaled to multiple replicas.
    acquired = await redis.set(LOCK_KEY, str(time.time()), nx=True, ex=LOCK_TTL_SECONDS)
    if not acquired:
        logger.debug("FXWatch poll skipped — another instance holds the lock")
        return

    for currency in PAIRS:
        await _poll_pair(redis, currency)


async def _poll_pair(redis: aioredis.Redis, currency: str) -> None:
    pair_label = f"MYR/{currency}"
    try:
        rate = await fetch_myr_rate(currency)
    except BNMError as exc:
        logger.error("FXWatch poll failed for %s: %s", pair_label, exc)
        return

    cache_key = f"{RATE_CACHE_PREFIX}{currency}"
    previous_raw = await redis.get(cache_key)

    snapshot = {
        "pair": pair_label,
        "rate": rate.middle_rate,
        "buying_rate": rate.buying_rate,
        "selling_rate": rate.selling_rate,
        "rate_date": rate.rate_date,
        "session": rate.session,
        "fetched_at": time.time(),
    }
    await redis.set(cache_key, json.dumps(snapshot), ex=3600)
    await redis.publish(f"fxwatch:updates:{currency}", json.dumps(snapshot))

    if previous_raw is None:
        return  # first tick ever — nothing to compare against yet

    try:
        previous_rate = float(json.loads(previous_raw)["rate"])
    except (KeyError, ValueError, TypeError):
        return
    if previous_rate == 0:
        return

    pct_change = ((rate.middle_rate - previous_rate) / previous_rate) * 100
    threshold = await get_threshold_pct(currency)

    if abs(pct_change) >= threshold:
        narrative = await generate_breach_narrative(
            pair=pair_label,
            previous_rate=previous_rate,
            current_rate=rate.middle_rate,
            pct_change=pct_change,
            threshold_pct=threshold,
        )
        delivery = await deliver_alert(f"\U0001f514 *{pair_label} corridor breach*\n{narrative}")
        logger.info(
            "FXWatch alert fired for %s (%.2f%% change): slack=%s telegram=%s",
            pair_label, pct_change, delivery["slack"], delivery["telegram"],
        )
