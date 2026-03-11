from typing import Any

from rag_ingest.agent_answer_assembler import assemble_answer
from rag_ingest.agent_answers import AgentAnswer
from rag_ingest.agno_tool_adapter import retrieve_knowledge


def answer_query(
    query: str,
    backend: Any,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
    rewrite_mode: str = 'none',
    history_mode: bool = False,
    include_debug: bool = False,
) -> AgentAnswer:
    retrieve_response = retrieve_knowledge(
        query=query,
        backend=backend,
        top_k=top_k,
        filters=filters,
        rewrite_mode=rewrite_mode,
        history_mode=history_mode,
        include_debug=include_debug,
    )
    return assemble_answer(
        query,
        retrieve_response,
        history_mode=history_mode,
    )
