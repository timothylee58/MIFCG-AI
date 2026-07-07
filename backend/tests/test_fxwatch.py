import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.fxwatch.bnm_client import BNMError, FXRate, fetch_myr_rate
from app.services.fxwatch.narrator import generate_breach_narrative
from app.services.fxwatch.notifiers import deliver_alert
from app.services.fxwatch.poller import poll_once


class FakeRedis:
    """Minimal in-memory stand-in for redis.asyncio.Redis, just enough for
    get/set(nx, ex)/publish used by the FXWatch poller and router."""

    def __init__(self):
        self.store: dict[str, str] = {}
        self.published: list[tuple[str, str]] = []

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    async def publish(self, channel, message):
        self.published.append((channel, message))
        return 1


def _bnm_payload(currency: str, middle=None, buying=None, selling=None, date="2026-07-06"):
    rate_entry = {"date": date}
    if buying is not None:
        rate_entry["buying_rate"] = buying
    if selling is not None:
        rate_entry["selling_rate"] = selling
    if middle is not None:
        rate_entry["middle_rate"] = middle
    return {"data": {"currency_code": currency, "unit": 1, "rate": [rate_entry]}}


# ─── BNM client ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_myr_rate_uses_middle_rate_when_present():
    payload = _bnm_payload("USD", middle=4.42, buying=4.41, selling=4.43)
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        rate = await fetch_myr_rate("USD")

    assert rate.currency == "USD"
    assert rate.middle_rate == 4.42
    assert rate.buying_rate == 4.41
    assert rate.selling_rate == 4.43


@pytest.mark.asyncio
async def test_fetch_myr_rate_falls_back_to_buy_sell_average():
    payload = _bnm_payload("SGD", middle=None, buying=3.20, selling=3.24)
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        rate = await fetch_myr_rate("SGD")

    assert rate.middle_rate == pytest.approx(3.22)


@pytest.mark.asyncio
async def test_fetch_myr_rate_raises_on_empty_rate_list():
    payload = {"data": {"currency_code": "USD", "unit": 1, "rate": []}}
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(BNMError):
            await fetch_myr_rate("USD")


@pytest.mark.asyncio
async def test_fetch_myr_rate_raises_on_http_error():
    with patch(
        "httpx.AsyncClient.get",
        new=AsyncMock(side_effect=httpx.ConnectTimeout("timed out")),
    ):
        with pytest.raises(BNMError):
            await fetch_myr_rate("USD")


# ─── Narrator ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_narrator_returns_haiku_text():
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "MYR strengthened sharply against USD."
    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        text = await generate_breach_narrative("MYR/USD", 4.45, 4.40, -1.12, 0.5)

    assert text == "MYR strengthened sharply against USD."


@pytest.mark.asyncio
async def test_narrator_falls_back_on_llm_error():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=Exception("down"))

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        text = await generate_breach_narrative("MYR/SGD", 3.20, 3.25, 1.56, 0.5)

    assert "MYR/SGD" in text
    assert "1.56" in text


# ─── Notifiers ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deliver_alert_skips_unconfigured_channels():
    with patch("app.services.fxwatch.notifiers.settings") as mock_settings:
        mock_settings.slack_webhook_url = ""
        mock_settings.telegram_bot_token = ""
        mock_settings.telegram_chat_id = ""
        result = await deliver_alert("test message")

    assert result == {"slack": False, "telegram": False}


@pytest.mark.asyncio
async def test_deliver_alert_sends_to_both_when_configured():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.fxwatch.notifiers.settings") as mock_settings:
        mock_settings.slack_webhook_url = "https://hooks.slack.test/abc"
        mock_settings.telegram_bot_token = "bot-token"
        mock_settings.telegram_chat_id = "12345"
        with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
            result = await deliver_alert("breach!")

    assert result == {"slack": True, "telegram": True}


# ─── Poller ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_poll_once_first_tick_caches_without_alert():
    fake_redis = FakeRedis()
    rate = FXRate(currency="USD", unit=1, middle_rate=4.40, buying_rate=4.39,
                  selling_rate=4.41, rate_date="2026-07-06", session="1130")

    async def _fake_get_redis():
        return fake_redis

    with patch("app.services.fxwatch.poller.get_redis", _fake_get_redis), \
         patch("app.services.fxwatch.poller.fetch_myr_rate", AsyncMock(return_value=rate)), \
         patch("app.services.fxwatch.poller.generate_breach_narrative") as mock_narrative, \
         patch("app.services.fxwatch.poller.deliver_alert") as mock_deliver:
        await poll_once()

    mock_narrative.assert_not_called()
    mock_deliver.assert_not_called()
    assert json.loads(fake_redis.store["fxwatch:rate:USD"])["rate"] == 4.40


@pytest.mark.asyncio
async def test_poll_once_triggers_alert_on_breach():
    fake_redis = FakeRedis()
    fake_redis.store["fxwatch:rate:USD"] = json.dumps({"rate": 4.40})
    fake_redis.store["fxwatch:rate:SGD"] = json.dumps({"rate": 3.20})
    breached_rate = FXRate(currency="USD", unit=1, middle_rate=4.50, buying_rate=4.49,
                           selling_rate=4.51, rate_date="2026-07-06", session="1130")
    unchanged_rate = FXRate(currency="SGD", unit=1, middle_rate=3.201, buying_rate=3.19,
                            selling_rate=3.21, rate_date="2026-07-06", session="1130")

    async def _fake_get_redis():
        return fake_redis

    async def _fake_fetch(currency, *a, **kw):
        return breached_rate if currency == "USD" else unchanged_rate

    with patch("app.services.fxwatch.poller.get_redis", _fake_get_redis), \
         patch("app.services.fxwatch.poller.fetch_myr_rate", _fake_fetch), \
         patch("app.services.fxwatch.poller.generate_breach_narrative",
               AsyncMock(return_value="narrative")) as mock_narrative, \
         patch("app.services.fxwatch.poller.deliver_alert",
               AsyncMock(return_value={"slack": True, "telegram": True})) as mock_deliver:
        await poll_once()

    # USD moved (4.50 - 4.40) / 4.40 = +2.27% >= default 0.5% threshold -> alert
    assert mock_narrative.call_count == 1
    assert mock_narrative.call_args.kwargs["pair"] == "MYR/USD"
    mock_deliver.assert_called_once()
    # SGD moved well under threshold -> no alert for it
    assert len(fake_redis.published) == 2  # both pairs still publish their tick


@pytest.mark.asyncio
async def test_poll_once_skips_when_lock_held():
    fake_redis = FakeRedis()
    fake_redis.store["fxwatch:poll-lock"] = "already-held"

    async def _fake_get_redis():
        return fake_redis

    with patch("app.services.fxwatch.poller.get_redis", _fake_get_redis), \
         patch("app.services.fxwatch.poller.fetch_myr_rate") as mock_fetch:
        await poll_once()

    mock_fetch.assert_not_called()


# ─── Router ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fxwatch_info_active():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/fxwatch/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "active"
    assert data["pairs"] == ["MYR/USD", "MYR/SGD"]


@pytest.mark.asyncio
async def test_get_rates_returns_cached_snapshot():
    fake_redis = FakeRedis()
    fake_redis.store["fxwatch:rate:USD"] = json.dumps({"pair": "MYR/USD", "rate": 4.42})
    fake_redis.store["fxwatch:rate:SGD"] = json.dumps({"pair": "MYR/SGD", "rate": 3.21})

    async def _fake_get_redis():
        return fake_redis

    with patch("app.services.fxwatch.poller.get_redis", _fake_get_redis):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/fxwatch/rates")

    assert r.status_code == 200
    rates = r.json()["rates"]
    assert len(rates) == 2
    assert {x["pair"] for x in rates} == {"MYR/USD", "MYR/SGD"}


@pytest.mark.asyncio
async def test_get_rates_live_fallback_when_cache_empty():
    fake_redis = FakeRedis()
    rate = FXRate(currency="USD", unit=1, middle_rate=4.42, buying_rate=4.41,
                  selling_rate=4.43, rate_date="2026-07-06", session="1130")

    async def _fake_get_redis():
        return fake_redis

    with patch("app.services.fxwatch.poller.get_redis", _fake_get_redis), \
         patch("app.routers.fxwatch.fetch_myr_rate", AsyncMock(return_value=rate)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/fxwatch/rates")

    assert r.status_code == 200
    assert len(r.json()["rates"]) == 2


@pytest.mark.asyncio
async def test_list_alert_thresholds_defaults():
    fake_redis = FakeRedis()

    async def _fake_get_redis():
        return fake_redis

    with patch("app.services.fxwatch.poller.get_redis", _fake_get_redis):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/fxwatch/alerts")

    assert r.status_code == 200
    thresholds = r.json()["thresholds"]
    assert {t["pair"]: t["threshold_pct"] for t in thresholds} == {
        "MYR/USD": 0.5, "MYR/SGD": 0.5,
    }


@pytest.mark.asyncio
async def test_create_alert_succeeds_as_admin():
    fake_redis = FakeRedis()

    async def _fake_get_redis():
        return fake_redis

    with patch("app.services.fxwatch.poller.get_redis", _fake_get_redis):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/api/fxwatch/alerts", json={"pair": "USD", "threshold_pct": 1.5}
            )

    assert r.status_code == 200
    assert r.json() == {"pair": "MYR/USD", "threshold_pct": 1.5}
    assert fake_redis.store["fxwatch:threshold:USD"] == "1.5"


@pytest.mark.asyncio
async def test_create_alert_rejects_unknown_pair():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/fxwatch/alerts", json={"pair": "EUR", "threshold_pct": 1.0}
        )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_requires_admin(real_auth):
    mock_user = MagicMock()
    mock_user.id = "viewer-user"
    mock_user.email = "viewer@example.com"
    mock_response = MagicMock()
    mock_response.user = mock_user

    mock_auth_sb = MagicMock()
    mock_auth_sb.auth.get_user.return_value = mock_response
    mock_role_result = MagicMock()
    mock_role_result.data = [{"role": "viewer"}]
    mock_auth_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_role_result
    )

    with patch("app.core.auth.get_supabase", return_value=mock_auth_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/api/fxwatch/alerts",
                headers={"Authorization": "Bearer good-token"},
                json={"pair": "USD", "threshold_pct": 1.0},
            )
    assert r.status_code == 403
