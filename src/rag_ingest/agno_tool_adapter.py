from typing import Any

from rag_ingest.retriever_tool import retrieve_tool


def retrieve_knowledge(
    query: str,
    backend: Any,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
    rewrite_mode: str = 'none',
    history_mode: bool = False,
    include_debug: bool = False,
) -> dict[str, Any]:
    return retrieve_tool(
        {
            'query': query,
            'top_k': top_k,
            'filters': filters or {},
            'rewrite_mode': rewrite_mode,
            'history_mode': history_mode,
            'include_debug': include_debug,
        },
        backend=backend,
    )
