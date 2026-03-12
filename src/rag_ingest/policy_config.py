import os


_ALLOWED_REWRITE_MODES = {
    'none',
    'rewrite_only',
    'multi_query',
    'rewrite_plus_multi_query',
}

_ALLOWED_RERANK_PROVIDERS = {
    'none',
    'http_qwen',
}

_ALLOWED_EMBEDDING_PROVIDERS = {
    'fastembed',
    'openai_compatible',
}

_ALLOWED_FALLBACK_MODES = {
    'lightweight',
    'none',
}


def _bool_from_env(value, default=False):
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 'yes', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'off'}:
        return False
    return default


def _safe_choice_with_reason(value, allowed, default):
    if value in (None, ''):
        return default, 'default'
    if value in allowed:
        return value, 'env'
    return default, 'invalid'


def load_policy_from_env(env=None):
    env = env or os.environ
    getter = env.get if hasattr(env, 'get') else lambda name, default=None: default

    rewrite_requested = getter('RAG_REWRITE_MODE')
    rerank_requested = getter('RAG_RERANKER_PROVIDER')
    embedding_requested = getter('RAG_EMBEDDING_PROVIDER')
    fallback_requested = getter('RAG_RETRIEVAL_FALLBACK_MODE')

    rewrite_mode, rewrite_reason = _safe_choice_with_reason(rewrite_requested, _ALLOWED_REWRITE_MODES, 'none')
    history_mode = _bool_from_env(getter('RAG_HISTORY_MODE'), default=False)
    rerank_provider, rerank_reason = _safe_choice_with_reason(rerank_requested, _ALLOWED_RERANK_PROVIDERS, 'none')
    embedding_provider, embedding_reason = _safe_choice_with_reason(embedding_requested, _ALLOWED_EMBEDDING_PROVIDERS, 'fastembed')
    fallback_mode, fallback_reason = _safe_choice_with_reason(fallback_requested, _ALLOWED_FALLBACK_MODES, 'lightweight')

    return {
        'rewrite_mode': rewrite_mode,
        'history_mode': history_mode,
        'rerank_provider': rerank_provider,
        'embedding_provider': embedding_provider,
        'fallback_mode': fallback_mode,
        'rewrite_requested': rewrite_requested,
        'rewrite_reason': rewrite_reason,
        'rerank_requested': rerank_requested,
        'rerank_reason': rerank_reason,
        'embedding_requested': embedding_requested,
        'embedding_reason': embedding_reason,
        'fallback_requested': fallback_requested,
        'fallback_reason': fallback_reason,
    }
