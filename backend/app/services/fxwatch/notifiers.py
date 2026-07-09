"""
Slack + Telegram delivery for FX corridor breach alerts. Both channels are
fired concurrently; a failure in one does not block the other.
"""

import asyncio
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _send_slack(message: str) -> bool:
    if not settings.slack_webhook_url:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(settings.slack_webhook_url, json={"text": message})
            resp.raise_for_status()
        return True
    except Exception as exc:
        logger.error("Slack delivery failed: %s", exc)
        return False


async def _send_telegram(message: str) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url, json={"chat_id": settings.telegram_chat_id, "text": message}
            )
            resp.raise_for_status()
        return True
    except Exception as exc:
        logger.error("Telegram delivery failed: %s", exc)
        return False


async def deliver_alert(message: str) -> dict:
    """Deliver `message` to Slack and Telegram concurrently. Returns per-channel success."""
    slack_ok, telegram_ok = await asyncio.gather(_send_slack(message), _send_telegram(message))
    return {"slack": slack_ok, "telegram": telegram_ok}
