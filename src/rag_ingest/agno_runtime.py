from typing import Any

from rag_ingest.agno_tool_adapter import retrieve_knowledge


_ALLOWED_REWRITE_MODES = {
    'none',
    'rewrite_only',
    'multi_query',
    'rewrite_plus_multi_query',
}


def _normalize_rewrite_mode(value: str | None, default: str) -> str:
    if not value or value not in _ALLOWED_REWRITE_MODES:
        return default
    return value


def build_agno_tools(
    backend: Any,
    default_top_k: int = 5,
    default_rewrite_mode: str = 'none',
    default_history_mode: bool = False,
    default_include_debug: bool = False,
) -> list:
    def retrieve_knowledge_tool(
        query: str,
        top_k: int = default_top_k,
        filters: dict[str, Any] | None = None,
        rewrite_mode: str | None = default_rewrite_mode,
        history_mode: bool = default_history_mode,
        include_debug: bool = default_include_debug,
    ) -> dict[str, Any]:
        return retrieve_knowledge(
            query=query,
            backend=backend,
            top_k=top_k,
            filters=filters,
            rewrite_mode=_normalize_rewrite_mode(rewrite_mode, default_rewrite_mode),
            history_mode=history_mode,
            include_debug=include_debug,
        )

    retrieve_knowledge_tool.__name__ = 'retrieve_knowledge'
    return [retrieve_knowledge_tool]


def create_agno_specialist_agent(
    backend: Any,
    instructions: str | None = None,
    markdown: bool = True,
    default_rewrite_mode: str = 'none',
    default_history_mode: bool = False,
    default_include_debug: bool = False,
    **kwargs: Any,
) -> Any:
    try:
        from agno.agent import Agent
    except ImportError as exc:
        raise RuntimeError('Agno is required to create the specialist agent runtime.') from exc

    return Agent(
        tools=build_agno_tools(
            backend=backend,
            default_rewrite_mode=default_rewrite_mode,
            default_history_mode=default_history_mode,
            default_include_debug=default_include_debug,
        ),
        instructions=instructions,
        markdown=markdown,
        **kwargs,
    )
