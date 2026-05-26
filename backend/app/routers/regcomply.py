from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/regcomply", tags=["regcomply"])


class ComplianceQuery(BaseModel):
    query: str
    sources: list[str] = []  # e.g. ["BNM", "SC", "PDPA"]
    stream: bool = True


@router.get("/")
async def regcomply_info():
    return {
        "module": "RegComply AI",
        "status": "scaffold",
        "description": "LangGraph RAG over BNM/SC/PDPA guidelines",
        "endpoints": ["/query", "/documents", "/ingest"],
    }


@router.post("/query")
async def query_compliance(body: ComplianceQuery):
    """Phase 1: Will stream LangGraph RAG answers. Stub for now."""
    raise HTTPException(
        status_code=501,
        detail="RegComply AI not yet implemented. Coming in Phase 1 (Week 2–3).",
    )


@router.get("/documents")
async def list_documents(source: str | None = None):
    """List ingested compliance documents."""
    raise HTTPException(status_code=501, detail="Phase 1.")
