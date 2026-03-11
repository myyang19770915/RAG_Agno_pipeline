from typing import Any

from rag_ingest.retriever_schemas import RetrieveResult


def build_citation(document_key: str, version_id: str, chunk_id: str) -> dict[str, str]:
    return {
        "document_key": document_key,
        "version_id": version_id,
        "chunk_id": chunk_id,
    }


def format_retrieve_result(
    *,
    text: str,
    score: float,
    document_key: str,
    version_id: str,
    chunk_id: str,
    metadata: dict[str, Any] | None = None,
) -> RetrieveResult:
    return RetrieveResult(
        text=text,
        score=score,
        document_key=document_key,
        version_id=version_id,
        chunk_id=chunk_id,
        metadata=metadata or {},
        citation=build_citation(document_key, version_id, chunk_id),
    )
