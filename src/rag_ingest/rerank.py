import os

from rag_ingest.http_reranker import HttpQwenReranker


def _optional_timeout(name, default=10):
    value = os.environ.get(name)
    if value in (None, ''):
        return default
    return float(value)


def _tokenize(text):
    return {token for token in text.lower().split() if token}


def rerank_candidates(query, candidates, strategy='lightweight'):
    if strategy == 'none':
        return list(candidates)

    if strategy == 'lightweight':
        query_tokens = _tokenize(query)
        return sorted(
            candidates,
            key=lambda candidate: (
                len(query_tokens & _tokenize(candidate.get('text', ''))),
                candidate.get('score', 0),
            ),
            reverse=True,
        )

    raise ValueError(f'Unsupported rerank strategy: {strategy}')


def select_reranker_from_env():
    provider_name = os.environ.get('RAG_RERANKER_PROVIDER', 'none')
    if provider_name == 'none':
        return None
    if provider_name == 'http_qwen':
        try:
            return HttpQwenReranker(
                base_url=os.environ.get('RAG_RERANKER_BASE_URL', 'http://127.0.0.1:8090'),
                model=os.environ.get('RAG_RERANKER_MODEL', 'Qwen/Qwen3-Reranker-0.6B'),
                api_key=os.environ.get('OPENAI_API_KEY') or None,
                timeout_seconds=_optional_timeout('RAG_RERANKER_TIMEOUT_SECONDS'),
            )
        except Exception:
            return None
    raise ValueError(f'Unsupported reranker provider: {provider_name}')
