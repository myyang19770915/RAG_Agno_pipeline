from dataclasses import dataclass, field


@dataclass
class PreparedQueries:
    applied_query: str
    applied_queries: list[str]
    rewrite_strategy: str
    rewrite_trace: dict[str, object] | None = None


def _normalize_query(query: str) -> str:
    return " ".join(query.lower().split())


def _expand_query(query: str) -> list[str]:
    expansions = [query]

    if "vpn" in query and "login" in query:
        expansions.append(query.replace("login", "sign in"))

    if len(expansions) == 1:
        expansions.append(f"{query} help")

    return expansions


def prepare_queries(query: str, rewrite_mode: str = 'none') -> PreparedQueries:
    if rewrite_mode == 'none':
        applied_query = query
        applied_queries = [query]
    elif rewrite_mode == 'rewrite_only':
        applied_query = _normalize_query(query)
        applied_queries = [applied_query]
    elif rewrite_mode == 'multi_query':
        applied_query = _normalize_query(query)
        applied_queries = _expand_query(applied_query)
    elif rewrite_mode == 'rewrite_plus_multi_query':
        applied_query = _normalize_query(query)
        applied_queries = _expand_query(applied_query)
    else:
        raise ValueError(f'Unsupported rewrite_mode: {rewrite_mode}')

    deduped_queries = list(dict.fromkeys(applied_queries))
    return PreparedQueries(
        applied_query=applied_query,
        applied_queries=deduped_queries,
        rewrite_strategy=rewrite_mode,
        rewrite_trace=None,
    )
