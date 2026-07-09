import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mifcg-api"


@pytest.mark.asyncio
async def test_regcomply_stub():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/regcomply/")
    assert response.status_code == 200
    assert response.json()["module"] == "RegComply AI"


@pytest.mark.asyncio
async def test_fxwatch_active():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/fxwatch/")
    assert response.status_code == 200
    assert "MYR/USD" in response.json()["pairs"]


@pytest.mark.asyncio
async def test_bursa_risk_stub():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/bursa-risk/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_survival_pro_stub():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/survival-pro/")
    assert response.status_code == 200
