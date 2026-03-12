from rag_ingest.policy_config import load_policy_from_env


def test_load_policy_from_env_returns_safe_defaults(monkeypatch):
    monkeypatch.delenv('RAG_REWRITE_MODE', raising=False)
    monkeypatch.delenv('RAG_HISTORY_MODE', raising=False)
    monkeypatch.delenv('RAG_RERANKER_PROVIDER', raising=False)
    monkeypatch.delenv('RAG_EMBEDDING_PROVIDER', raising=False)
    monkeypatch.delenv('RAG_RETRIEVAL_FALLBACK_MODE', raising=False)

    policy = load_policy_from_env()

    assert policy == {
        'rewrite_mode': 'none',
        'history_mode': False,
        'rerank_provider': 'none',
        'embedding_provider': 'fastembed',
        'fallback_mode': 'lightweight',
        'rewrite_requested': None,
        'rewrite_reason': 'default',
        'rerank_requested': None,
        'rerank_reason': 'default',
        'embedding_requested': None,
        'embedding_reason': 'default',
        'fallback_requested': None,
        'fallback_reason': 'default',
    }


def test_load_policy_from_env_reads_explicit_env_values(monkeypatch):
    monkeypatch.setenv('RAG_REWRITE_MODE', 'multi_query')
    monkeypatch.setenv('RAG_HISTORY_MODE', 'true')
    monkeypatch.setenv('RAG_RERANKER_PROVIDER', 'http_qwen')
    monkeypatch.setenv('RAG_EMBEDDING_PROVIDER', 'openai_compatible')
    monkeypatch.setenv('RAG_RETRIEVAL_FALLBACK_MODE', 'none')

    policy = load_policy_from_env()

    assert policy == {
        'rewrite_mode': 'multi_query',
        'history_mode': True,
        'rerank_provider': 'http_qwen',
        'embedding_provider': 'openai_compatible',
        'fallback_mode': 'none',
        'rewrite_requested': 'multi_query',
        'rewrite_reason': 'env',
        'rerank_requested': 'http_qwen',
        'rerank_reason': 'env',
        'embedding_requested': 'openai_compatible',
        'embedding_reason': 'env',
        'fallback_requested': 'none',
        'fallback_reason': 'env',
    }


def test_load_policy_from_env_falls_back_for_unsafe_values(monkeypatch):
    monkeypatch.setenv('RAG_REWRITE_MODE', 'summarize_only')
    monkeypatch.setenv('RAG_HISTORY_MODE', 'maybe')
    monkeypatch.setenv('RAG_RERANKER_PROVIDER', 'custom_llm')
    monkeypatch.setenv('RAG_EMBEDDING_PROVIDER', 'remote_gpu')
    monkeypatch.setenv('RAG_RETRIEVAL_FALLBACK_MODE', 'eventual')

    policy = load_policy_from_env()

    assert policy == {
        'rewrite_mode': 'none',
        'history_mode': False,
        'rerank_provider': 'none',
        'embedding_provider': 'fastembed',
        'fallback_mode': 'lightweight',
        'rewrite_requested': 'summarize_only',
        'rewrite_reason': 'invalid',
        'rerank_requested': 'custom_llm',
        'rerank_reason': 'invalid',
        'embedding_requested': 'remote_gpu',
        'embedding_reason': 'invalid',
        'fallback_requested': 'eventual',
        'fallback_reason': 'invalid',
    }
