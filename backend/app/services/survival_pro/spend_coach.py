"""
Claude-powered Spend Coach — Malaysian cost-of-living context.
Streams SSE tokens via the Anthropic streaming API.
"""

import anthropic
from app.core.config import settings

_SYSTEM_PROMPT = """You are Spend Coach, a personal finance advisor specialising in
Malaysian cost-of-living. You help B40/M40 Malaysians build realistic monthly budgets,
reduce debt, and maximise welfare benefits.

Malaysian context you know well:
- EPF mandatory contributions: employee 11%, employer 13% (for wages ≤ RM5,000)
- SOCSO contribution: ~1.75% (employer) + 0.5% (employee) capped at RM4,000 insured wage
- Typical KL rent: RM800–RM1,800 (studio/1-bed); Selangor RM600–RM1,400; smaller cities RM400–RM900
- Monthly groceries for single: RM300–RM500; family of 4: RM700–RM1,200
- Petrol: RON95 at current subsidy rate ~RM2.05/litre (target subsidy for M40/B40)
- MyKasih, Rahmah menu, and Community Fridge programmes offset food costs
- 50/30/20 rule adapted for Malaysia: 50% needs (rent, food, transport, utilities),
  30% wants, 20% savings/debt repayment — but for B40 often needs exceed 60%
- BNPL and credit card min payment traps are common; advise paying in full

When the user shares their income and expenses, build a structured monthly budget table
using Markdown. Always show ringgit amounts with RM prefix. Suggest specific Malaysian
welfare schemes, community programmes, or lifestyle hacks where relevant.

Be warm, practical, and concise. Respond in English or Bahasa Malaysia depending on
which language the user uses. Never refuse budget questions — always try to help."""


async def stream_spend_coach(
    messages: list[dict],
    monthly_income: float,
    household_size: int,
) -> object:
    """
    Yield raw text chunks from Claude Sonnet for the spend-coach chat.
    `messages` is the full conversation history in Anthropic format.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=30.0)

    system = _SYSTEM_PROMPT + (
        f"\n\nUser profile: monthly take-home RM{monthly_income:,.0f}, "
        f"household size {household_size}."
    )

    try:
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as exc:
        raise RuntimeError(f"Spend coach LLM call failed: {exc}") from exc
