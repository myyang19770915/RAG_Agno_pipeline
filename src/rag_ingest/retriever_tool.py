from dataclasses import asdict
from typing import Any

from rag_ingest.retriever_core import retrieve
from rag_ingest.retriever_schemas import RetrieveRequest


def retrieve_tool(request_dict: dict[str, Any], backend: Any) -> dict[str, Any]:
    request = RetrieveRequest(**request_dict)
    response = retrieve(
        request.query,
        backend=backend,
        top_k=request.top_k,
        rewrite_mode=request.rewrite_mode,
        history_mode=request.history_mode,
        filters=request.filters,
        include_debug=request.include_debug,
    )
    return asdict(response)
