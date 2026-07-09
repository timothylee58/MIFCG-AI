import hashlib
import json
import logging
import tempfile
import os
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.core.auth import get_current_user, require_admin
from app.core.limiter import limiter
from app.core.redis import get_redis
from app.services.regcomply import rag_graph, ingest_pdf

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/regcomply",
    tags=["regcomply"],
    dependencies=[Depends(get_current_user)],
)

CACHE_TTL = 3600  # 1 hour
VALID_SOURCES = {"BNM", "SC", "PDPA", "BURSA"}


class ComplianceQuery(BaseModel):
    query: str
    sources: list[str] = []


def _cache_key(query: str, sources: list[str]) -> str:
    canonical = f"{query.strip().lower()}:{sorted(sources)}"
    return f"regcomply:{hashlib.sha256(canonical.encode()).hexdigest()[:24]}"


@router.get("/")
async def regcomply_info():
    return {
        "module": "RegComply AI",
        "status": "active",
        "pipeline": "router → retriever → synthesizer",
        "sources": list(VALID_SOURCES),
    }


@router.post("/query")
@limiter.limit("20/minute")
async def query_compliance(request: Request, body: ComplianceQuery):
    """
    SSE-streaming compliance query.

    Event stream format:
      data: {"type": "routing",    "sources": [...]}
      data: {"type": "retrieving", "count": N}
      data: {"type": "chunk",      "content": "..."}   ← repeated for each token
      data: {"type": "citations",  "citations": [...]}
      data: {"type": "done"}
      data: {"type": "error",      "message": "..."}
    """
    if not body.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty.")

    sources = [s.upper() for s in body.sources if s.upper() in VALID_SOURCES]
    cache_key = _cache_key(body.query, sources)

    async def event_stream():
        # ── Cache check ────────────────────────────────────────────────
        try:
            redis = await get_redis()
            cached = await redis.get(cache_key)
            if cached:
                payload = json.loads(cached)
                yield {"data": json.dumps({"type": "chunk", "content": payload["answer"]})}
                yield {"data": json.dumps({"type": "citations", "citations": payload["citations"]})}
                yield {"data": json.dumps({"type": "done", "cached": True})}
                return
        except Exception:
            pass  # Redis unavailable — proceed without cache

        # ── LangGraph streaming via astream_events ─────────────────────
        answer_parts: list[str] = []
        final_citations: list[dict] = []
        routed: list[str] = []
        chunk_count = 0

        try:
            async for event in rag_graph.astream_events(
                {"query": body.query, "sources": sources, "error": None},
                version="v2",
            ):
                kind = event["event"]
                name = event.get("name", "")

                # Router finished → tell client which sources we're searching
                if kind == "on_chain_end" and name == "router":
                    routed = event["data"]["output"].get("routed_sources", [])
                    yield {"data": json.dumps({"type": "routing", "sources": routed})}

                # Retriever finished → tell client how many chunks found
                elif kind == "on_chain_end" and name == "retriever":
                    chunk_count = len(event["data"]["output"].get("chunks", []))
                    yield {"data": json.dumps({"type": "retrieving", "count": chunk_count})}

                # LLM streaming token from the synthesizer
                elif kind == "on_chat_model_stream":
                    token = event["data"]["chunk"].content
                    if token:
                        answer_parts.append(token)
                        yield {"data": json.dumps({"type": "chunk", "content": token})}

                # Synthesizer finished → emit citations
                elif kind == "on_chain_end" and name == "synthesizer":
                    final_citations = event["data"]["output"].get("citations", [])
                    yield {"data": json.dumps({"type": "citations", "citations": final_citations})}

            # ── Cache the completed answer ──────────────────────────────
            full_answer = "".join(answer_parts)
            try:
                redis = await get_redis()
                await redis.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps({"answer": full_answer, "citations": final_citations}),
                )
            except Exception:
                pass

            yield {"data": json.dumps({"type": "done", "cached": False})}

        except Exception as exc:
            logger.exception("RAG pipeline error")
            yield {"data": json.dumps({"type": "error", "message": str(exc)})}

    return EventSourceResponse(event_stream())


@router.get("/documents")
async def list_documents(source: str | None = None):
    """List all ingested compliance documents."""
    from app.core.supabase import get_supabase
    sb = get_supabase()
    q = sb.table("compliance_documents").select("id, title, source, ingested_at, chunk_count")
    if source:
        q = q.eq("source", source.upper())
    result = q.order("ingested_at", desc=True).execute()
    return {"documents": result.data or []}


@router.post("/ingest", dependencies=[Depends(require_admin)])
@limiter.limit("20/minute")
async def ingest_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    source: str = Form(...),
):
    """Upload and ingest a PDF compliance document into pgvector."""
    source = source.upper()
    if source not in VALID_SOURCES:
        raise HTTPException(status_code=422, detail=f"Source must be one of {VALID_SOURCES}")
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are supported.")

    # Write to temp file (PyPDFLoader requires a file path)
    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = await ingest_pdf(file_path=tmp_path, title=title, source=source)
    finally:
        os.unlink(tmp_path)

    return result
