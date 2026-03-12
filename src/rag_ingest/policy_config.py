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


def _bool_from_env(value, default=False):
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 'yes', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'off'}:
        return False
    return default


def _safe_choice(value, allowed, default):
    if value in allowed:
        return value
    return default


def load_policy_from_env(env=None):
    env = env or os.environ
    getter = env.get if hasattr(env, 'get') else lambda name, default=None: default

    rewrite_mode = _safe_choice(getter('RAG_REWRITE_MODE'), _ALLOWED_REWRITE_MODES, 'none')
    history_mode = _bool_from_env(getter('RAG_HISTORY_MODE'), default=False)
    rerank_provider = _safe_choice(getter('RAG_RERANKER_PROVIDER'), _ALLOWED_RERANK_PROVIDERS, 'none')
    embedding_provider = _safe_choice(getter('RAG_EMBEDDING_PROVIDER'), _ALLOWED_EMBEDDING_PROVIDERS, 'fastembed')

    return {
        'rewrite_mode': rewrite_mode,
        'history_mode': history_mode,
        'rerank_provider': rerank_provider,
        'embedding_provider': embedding_provider,
    }
