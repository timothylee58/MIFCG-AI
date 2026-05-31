"""
Ingest a PDF compliance document into Supabase pgvector.

Usage (from FastAPI route or CLI):
    result = await ingest_pdf(
        file_bytes=pdf_bytes,
        title="BNM AML/CFT Policy Document 2024",
        source="BNM",
    )
"""

import uuid
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.supabase import get_supabase
from .embeddings import get_embeddings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


async def ingest_pdf(
    file_path: str,
    title: str,
    source: str,
    file_url: str | None = None,
) -> dict:
    """
    Load a PDF, chunk it, embed all chunks, and upsert into Supabase.
    Returns a summary dict with document_id and chunk_count.
    """
    supabase = get_supabase()

    # 1. Load + split PDF
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    raw_chunks = splitter.split_documents(pages)
    logger.info("Loaded %d chunks from '%s'", len(raw_chunks), title)

    # 2. Create document record
    doc_id = str(uuid.uuid4())
    supabase.table("compliance_documents").upsert({
        "id": doc_id,
        "title": title,
        "source": source,
        "file_url": file_url,
        "chunk_count": len(raw_chunks),
    }).execute()

    # 3. Embed all chunk texts (batch for efficiency)
    embeddings_model = get_embeddings()
    texts = [c.page_content for c in raw_chunks]
    vectors = await embeddings_model.aembed_documents(texts)

    # 4. Upsert chunks into pgvector table
    rows = [
        {
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "content": texts[i],
            "embedding": vectors[i],
            "chunk_index": i,
            "metadata": {
                "page": raw_chunks[i].metadata.get("page", 0),
                "source_file": raw_chunks[i].metadata.get("source", ""),
            },
        }
        for i in range(len(raw_chunks))
    ]

    # Insert in batches of 100 to stay within Supabase request limits
    batch_size = 100
    for start in range(0, len(rows), batch_size):
        supabase.table("document_chunks").upsert(rows[start : start + batch_size]).execute()

    # 5. Mark document as ingested
    from datetime import datetime, timezone
    supabase.table("compliance_documents").update({
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", doc_id).execute()

    logger.info("Ingested document '%s' (%d chunks)", title, len(rows))
    return {"document_id": doc_id, "chunk_count": len(rows), "title": title, "source": source}
