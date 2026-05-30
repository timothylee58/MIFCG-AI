import json
import logging
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from .state import RegComplyState
from .retriever import similarity_search
from .prompts import ROUTER_SYSTEM, SYNTHESIZER_SYSTEM

logger = logging.getLogger(__name__)

VALID_SOURCES = {"BNM", "SC", "PDPA", "BURSA"}

_router_llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=settings.anthropic_api_key,
    max_tokens=64,
    temperature=0,
)

_synthesizer_llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    max_tokens=2048,
    temperature=0.1,
    streaming=True,
)


async def router_node(state: RegComplyState) -> dict:
    """Classify query → select which regulatory sources to search."""
    user_sources = set(s.upper() for s in state.get("sources", []) if s.upper() in VALID_SOURCES)

    # If user explicitly specified all sources, skip LLM routing
    if user_sources:
        return {"routed_sources": sorted(user_sources), "error": None}

    try:
        response = await _router_llm.ainvoke([
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=state["query"]),
        ])
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        routed = json.loads(raw)
        valid = [s for s in routed if s in VALID_SOURCES]
        return {"routed_sources": valid or ["BNM", "SC"], "error": None}
    except Exception as exc:
        logger.warning("Router LLM failed, defaulting to BNM+SC: %s", exc)
        return {"routed_sources": ["BNM", "SC"], "error": None}


async def retriever_node(state: RegComplyState) -> dict:
    """pgvector similarity search over compliance document chunks."""
    sources = state.get("routed_sources") or ["BNM", "SC"]
    try:
        chunks = await similarity_search(
            query=state["query"],
            sources=sources,
            match_count=8,
            match_threshold=0.5,
        )
        return {"chunks": chunks, "error": None}
    except Exception as exc:
        logger.error("Retriever failed: %s", exc)
        return {"chunks": [], "error": str(exc)}


def _format_context(chunks: list[dict]) -> str:
    """Format chunks for the synthesizer prompt with citation labels."""
    if not chunks:
        return "No relevant document excerpts found."
    lines = []
    for i, chunk in enumerate(chunks, 1):
        label = f"[{chunk.get('doc_source', 'DOC')}-{i}]"
        title = chunk.get("doc_title", "Unknown Document")
        sim = chunk.get("similarity", 0)
        lines.append(
            f"{label} {title} (relevance: {sim:.0%})\n{chunk['content']}\n"
        )
    return "\n---\n".join(lines)


async def synthesizer_node(state: RegComplyState) -> dict:
    """Generate a streamed, citation-backed compliance answer."""
    chunks = state.get("chunks", [])
    context = _format_context(chunks)

    user_prompt = (
        f"Query: {state['query']}\n\n"
        f"Context chunks:\n{context}"
    )

    # Build citations list from retrieved chunks
    citations = [
        {
            "label": f"[{c.get('doc_source', 'DOC')}-{i}]",
            "title": c.get("doc_title", "Unknown"),
            "source": c.get("doc_source", ""),
            "doc_id": c.get("document_id", ""),
            "similarity": round(c.get("similarity", 0), 3),
        }
        for i, c in enumerate(chunks, 1)
    ]

    try:
        response = await _synthesizer_llm.ainvoke([
            SystemMessage(content=SYNTHESIZER_SYSTEM),
            HumanMessage(content=user_prompt),
        ])
        return {
            "answer": response.content,
            "citations": citations,
            "error": None,
        }
    except Exception as exc:
        logger.error("Synthesizer failed: %s", exc)
        return {
            "answer": "I encountered an error generating the compliance answer. Please try again.",
            "citations": [],
            "error": str(exc),
        }
