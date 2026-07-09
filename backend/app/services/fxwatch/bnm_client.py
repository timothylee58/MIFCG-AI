"""
Thin async client for Bank Negara Malaysia's public Open API.

Portal: https://apikijangportal.bnm.gov.my/openapi (no formal machine-readable
schema published). Endpoint shape confirmed against community wrappers that
call the live API:

    GET https://api.bnm.gov.my/public/exchange-rate/{currency}
    Accept: application/vnd.BNM.API.v1+json
    ?session=1130&quote=rm

    {
      "data": {
        "currency_code": "USD",
        "unit": 1,
        "rate": [
          {"date": "2026-07-06", "buying_rate": 4.4123,
           "selling_rate": 4.4325, "middle_rate": 4.4224},
          ...
        ]
      }
    }

No API key required. `quote=rm` means the rate is expressed as MYR per
`unit` of the foreign currency. We take the last entry in `rate` as the
latest available quote for the requested session.
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

BNM_API_BASE = "https://api.bnm.gov.my/public"
_HEADERS = {"Accept": "application/vnd.BNM.API.v1+json"}

# BNM publishes rates at these fixed snapshot times each trading day.
VALID_SESSIONS = {"0900", "1130", "1200", "1700"}
DEFAULT_SESSION = "1130"


class BNMError(RuntimeError):
    """Raised when the BNM API is unreachable or returns an unexpected shape."""


@dataclass
class FXRate:
    currency: str            # ISO 4217, e.g. "USD"
    unit: float               # units of foreign currency the rate is quoted per
    middle_rate: float        # MYR per `unit` of foreign currency
    buying_rate: float | None
    selling_rate: float | None
    rate_date: str | None
    session: str


async def fetch_myr_rate(currency: str, session: str = DEFAULT_SESSION) -> FXRate:
    """
    Fetch the latest MYR rate for `currency` (ISO 4217 code, e.g. "USD", "SGD").
    """
    session = session if session in VALID_SESSIONS else DEFAULT_SESSION
    url = f"{BNM_API_BASE}/exchange-rate/{currency.upper()}"
    params = {"session": session, "quote": "rm"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=_HEADERS, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        raise BNMError(f"BNM API request failed for {currency}: {exc}") from exc

    try:
        data = payload["data"]
        rates = data["rate"]
        if not rates:
            raise BNMError(f"BNM API returned no rate entries for {currency}")
        latest = rates[-1]

        middle = latest.get("middle_rate")
        buying = latest.get("buying_rate")
        selling = latest.get("selling_rate")
        if middle is None:
            if buying is None or selling is None:
                raise BNMError(
                    f"BNM API response missing rate fields for {currency}: {latest}"
                )
            middle = (buying + selling) / 2

        return FXRate(
            currency=data.get("currency_code", currency.upper()),
            unit=data.get("unit", 1),
            middle_rate=float(middle),
            buying_rate=float(buying) if buying is not None else None,
            selling_rate=float(selling) if selling is not None else None,
            rate_date=latest.get("date"),
            session=session,
        )
    except BNMError:
        raise
    except (KeyError, TypeError, IndexError) as exc:
        raise BNMError(f"Unexpected BNM API response shape for {currency}: {exc}") from exc
