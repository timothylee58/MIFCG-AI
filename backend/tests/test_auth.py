import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app


# NOTE: the autouse `_override_auth` fixture in conftest.py stubs out
# get_current_user/require_admin for every test in the suite so business
# logic tests don't need real JWTs. These tests specifically want to
# exercise the *real* dependency, so they use the `real_auth` fixture
# (also in conftest.py) to remove the override for their duration.


@pytest.mark.asyncio
async def test_protected_route_without_auth_header_is_401(real_auth):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/regcomply/")
    assert r.status_code == 401
    assert r.json()["detail"] == "Missing authorization header"


@pytest.mark.asyncio
async def test_protected_route_with_malformed_header_is_401(real_auth):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/regcomply/", headers={"Authorization": "Token abc123"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token_is_401(real_auth):
    mock_sb = MagicMock()
    mock_sb.auth.get_user.side_effect = Exception("invalid jwt")

    with patch("app.core.auth.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(
                "/api/regcomply/", headers={"Authorization": "Bearer bad-token"}
            )
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_protected_route_with_valid_token_succeeds(real_auth):
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "viewer@example.com"
    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_sb = MagicMock()
    mock_sb.auth.get_user.return_value = mock_response

    with patch("app.core.auth.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(
                "/api/regcomply/", headers={"Authorization": "Bearer good-token"}
            )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_health_does_not_require_auth(real_auth):
    """Health checks must stay unauthenticated for Railway's healthcheck probe."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_ingest_requires_admin_role(real_auth):
    """A valid but non-admin user must get 403 on the admin-only ingest route."""
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
                "/api/regcomply/ingest",
                headers={"Authorization": "Bearer good-token"},
                files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
                data={"title": "Test Doc", "source": "BNM"},
            )
    assert r.status_code == 403
    assert r.json()["detail"] == "Admin access required"
