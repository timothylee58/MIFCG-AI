from app.core.supabase import get_supabase
from .embeddings import embed_query


async def similarity_search(
    query: str,
    sources: list[str],
    match_count: int = 8,
    match_threshold: float = 0.5,
) -> list[dict]:
    embedding = await embed_query(query)
    supabase = get_supabase()

    # Call the match_document_chunks SQL function
    result = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
            "filter_source": sources[0] if len(sources) == 1 else None,
        },
    ).execute()

    chunks = result.data or []

    # If multiple sources, filter client-side (Supabase RPC doesn't support IN easily)
    if len(sources) > 1:
        # Re-fetch per source and merge, deduplicating by chunk id
        all_chunks: dict[str, dict] = {}
        for source in sources:
            sub = supabase.rpc(
                "match_document_chunks",
                {
                    "query_embedding": embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count,
                    "filter_source": source,
                },
            ).execute()
            for chunk in (sub.data or []):
                all_chunks[chunk["id"]] = chunk
        chunks = sorted(all_chunks.values(), key=lambda c: c["similarity"], reverse=True)[
            :match_count
        ]

    # Enrich each chunk with document title
    if chunks:
        doc_ids = list({c["document_id"] for c in chunks})
        docs_result = (
            supabase.table("compliance_documents")
            .select("id, title, source")
            .in_("id", doc_ids)
            .execute()
        )
        doc_map = {d["id"]: d for d in (docs_result.data or [])}
        for chunk in chunks:
            doc = doc_map.get(chunk["document_id"], {})
            chunk["doc_title"] = doc.get("title", "Unknown")
            chunk["doc_source"] = doc.get("source", "")

    return chunks
