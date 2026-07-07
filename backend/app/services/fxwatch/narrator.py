"""
Claude Haiku narrative generation for FX corridor breach alerts.
"""

import logging

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an FX desk analyst writing a one-paragraph alert for a
corridor breach in a Malaysian Ringgit (MYR) currency pair. Given the pair, the
previous rate, the new rate, and the percentage move, write a short (2-3 sentence),
plain-English narrative a trader can read in under 10 seconds. State the direction
of the move (MYR strengthening/weakening), the magnitude, and one plausible
practical implication (e.g. import costs, remittance timing, hedging). Do not
speculate on unannounced central bank decisions. No preamble, no sign-off — just
the narrative."""


async def generate_breach_narrative(
    pair: str,
    previous_rate: float,
    current_rate: float,
    pct_change: float,
    threshold_pct: float,
) -> str:
    """Generate a short Claude Haiku narrative for a threshold-breaching FX move."""
    direction = "strengthened" if current_rate < previous_rate else "weakened"

    user_prompt = (
        f"Pair: {pair}\n"
        f"Previous rate: {previous_rate:.4f}\n"
        f"Current rate: {current_rate:.4f}\n"
        f"Change: {pct_change:+.2f}% (MYR has {direction})\n"
        f"Configured alert threshold: {threshold_pct:.2f}%"
    )

    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=15.0)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        for block in response.content:
            if block.type == "text":
                return block.text.strip()
        raise ValueError("No text content block in Anthropic response")
    except Exception as exc:
        logger.warning("Haiku narrative generation failed, using fallback: %s", exc)
        return (
            f"{pair} moved {pct_change:+.2f}% — MYR has {direction} from "
            f"{previous_rate:.4f} to {current_rate:.4f}, breaching the "
            f"{threshold_pct:.2f}% alert threshold."
        )
