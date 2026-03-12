from rag_ingest.policy_config import load_policy_from_env


def test_load_policy_from_env_returns_safe_defaults(monkeypatch):
    monkeypatch.delenv('RAG_REWRITE_MODE', raising=False)
    monkeypatch.delenv('RAG_HISTORY_MODE', raising=False)
    monkeypatch.delenv('RAG_RERANKER_PROVIDER', raising=False)
    monkeypatch.delenv('RAG_EMBEDDING_PROVIDER', raising=False)

    policy = load_policy_from_env()

    assert policy == {
        'rewrite_mode': 'none',
        'history_mode': False,
        'rerank_provider': 'none',
        'embedding_provider': 'fastembed',
    }


def test_load_policy_from_env_reads_explicit_env_values(monkeypatch):
    monkeypatch.setenv('RAG_REWRITE_MODE', 'multi_query')
    monkeypatch.setenv('RAG_HISTORY_MODE', 'true')
    monkeypatch.setenv('RAG_RERANKER_PROVIDER', 'http_qwen')
    monkeypatch.setenv('RAG_EMBEDDING_PROVIDER', 'openai_compatible')

    policy = load_policy_from_env()

    assert policy == {
        'rewrite_mode': 'multi_query',
        'history_mode': True,
        'rerank_provider': 'http_qwen',
        'embedding_provider': 'openai_compatible',
    }


def test_load_policy_from_env_falls_back_for_unsafe_values(monkeypatch):
    monkeypatch.setenv('RAG_REWRITE_MODE', 'summarize_only')
    monkeypatch.setenv('RAG_HISTORY_MODE', 'maybe')
    monkeypatch.setenv('RAG_RERANKER_PROVIDER', 'custom_llm')
    monkeypatch.setenv('RAG_EMBEDDING_PROVIDER', 'remote_gpu')

    policy = load_policy_from_env()

    assert policy == {
        'rewrite_mode': 'none',
        'history_mode': False,
        'rerank_provider': 'none',
        'embedding_provider': 'fastembed',
    }
