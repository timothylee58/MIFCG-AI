from typing import TypedDict


class RegComplyState(TypedDict):
    query: str
    sources: list[str]          # user-specified filters e.g. ["BNM", "SC"]
    routed_sources: list[str]   # router's final selection
    chunks: list[dict]          # retrieved pgvector chunks
    answer: str                 # synthesized answer text
    citations: list[dict]       # [{title, source, doc_id, similarity}]
    error: str | None
