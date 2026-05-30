import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_regcomply_info():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/regcomply/")
    assert r.status_code == 200
    assert r.json()["status"] == "active"


@pytest.mark.asyncio
async def test_query_empty_body():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/regcomply/query", json={"query": "  ", "sources": []})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_documents_stub():
    """list_documents calls Supabase — mock the client."""
    mock_result = MagicMock()
    mock_result.data = []
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = mock_result

    with patch("app.core.supabase.get_supabase", return_value=mock_sb):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/regcomply/documents")
    assert r.status_code == 200
    assert r.json()["documents"] == []


@pytest.mark.asyncio
async def test_router_node_defaults_on_error():
    """Router should default to BNM+SC when LLM fails."""
    from app.services.regcomply.nodes import router_node
    with patch("app.services.regcomply.nodes._router_llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM unavailable"))
        result = await router_node({"query": "What is AML?", "sources": [], "error": None,
                                    "routed_sources": [], "chunks": [], "answer": "", "citations": []})
    assert set(result["routed_sources"]) == {"BNM", "SC"}


@pytest.mark.asyncio
async def test_router_node_respects_user_sources():
    """If the user specified sources, the router should skip LLM and use them."""
    from app.services.regcomply.nodes import router_node
    result = await router_node({"query": "PDPA question", "sources": ["PDPA"],
                                 "error": None, "routed_sources": [], "chunks": [],
                                 "answer": "", "citations": []})
    assert result["routed_sources"] == ["PDPA"]
