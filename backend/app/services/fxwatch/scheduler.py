"""APScheduler wiring for FXWatch's periodic BNM rate poll."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from .poller import poll_once

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_fxwatch_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        poll_once,
        "interval",
        minutes=settings.fx_poll_interval_minutes,
        id="fxwatch-poll",
        max_instances=1,
    )
    _scheduler.start()
    logger.info("FXWatch scheduler started (every %s min)", settings.fx_poll_interval_minutes)
    return _scheduler


def stop_fxwatch_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
