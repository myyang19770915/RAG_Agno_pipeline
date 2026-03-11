import os

from rag_ingest.embedding_provider import (
    DeterministicEmbeddingProvider,
    select_embedding_provider,
)
from rag_ingest.http_embedding_adapter import HttpEmbeddingAdapter


def test_deterministic_provider_returns_fixed_dim_vectors():
    provider = DeterministicEmbeddingProvider(dims=4)
    vectors = provider.embed_texts(['hello', 'world'])
    assert len(vectors) == 2
    assert len(vectors[0]) == 4


def test_select_provider_falls_back_without_api_key():
    old = os.environ.pop('OPENAI_API_KEY', None)
    old_provider = os.environ.pop('RAG_EMBEDDING_PROVIDER', None)
    try:
        provider = select_embedding_provider()
        assert provider.name == 'deterministic-local'
    finally:
        if old is not None:
            os.environ['OPENAI_API_KEY'] = old
        if old_provider is not None:
            os.environ['RAG_EMBEDDING_PROVIDER'] = old_provider


def test_select_provider_supports_openai_compatible_env_names(monkeypatch):
    monkeypatch.setenv('RAG_EMBEDDING_PROVIDER', 'openai_compatible')
    monkeypatch.setenv('RAG_EMBEDDING_BASE_URL', 'http://localhost:8000/v1')
    monkeypatch.setenv('RAG_EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-0.6B')

    provider = select_embedding_provider()

    assert isinstance(provider, HttpEmbeddingAdapter)
    assert provider.base_url == 'http://localhost:8000/v1'
    assert provider.model == 'Qwen/Qwen3-Embedding-0.6B'
