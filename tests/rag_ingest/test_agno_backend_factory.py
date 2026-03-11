import pytest

from rag_ingest.agno_backend_factory import create_backend_from_env, resolve_backend_options_from_env
from rag_ingest.query_encoders import RuntimeQueryEncoder


class FakeBackend:
    pass


class RecordingBuilder:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return FakeBackend()


def test_create_backend_from_env_requires_minimal_runtime_settings(monkeypatch):
    for key in [
        'RAG_QDRANT_URL',
        'RAG_QDRANT_COLLECTION',
        'RAG_DENSE_MODEL',
        'RAG_SPARSE_MODEL',
    ]:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(RuntimeError, match='Missing required Agno backend settings'):
        create_backend_from_env()


def test_create_backend_from_env_delegates_to_injected_builder(monkeypatch):
    monkeypatch.setenv('RAG_QDRANT_URL', 'http://localhost:6333')
    monkeypatch.setenv('RAG_QDRANT_COLLECTION', 'documents')
    monkeypatch.setenv('RAG_DENSE_MODEL', 'dense-model')
    monkeypatch.setenv('RAG_SPARSE_MODEL', 'sparse-model')
    monkeypatch.setenv('RAG_FASTEMBED_CACHE_DIR', '/tmp/fastembed')
    monkeypatch.setenv('RAG_FASTEMBED_THREADS', '4')

    builder = RecordingBuilder()

    backend = create_backend_from_env(builder=builder)

    assert isinstance(backend, FakeBackend)
    assert builder.calls == [
        {
            'qdrant_url': 'http://localhost:6333',
            'collection_name': 'documents',
            'dense_model': 'dense-model',
            'sparse_model': 'sparse-model',
            'cache_dir': '/tmp/fastembed',
            'threads': 4,
            'embedding_provider': 'fastembed',
            'embedding_base_url': None,
            'embedding_model': None,
            'reranker_provider': 'none',
            'reranker_base_url': None,
            'reranker_model': None,
        }
    ]


def test_create_backend_from_env_allows_openai_compatible_embedding_without_dense_model(monkeypatch):
    monkeypatch.setenv('RAG_QDRANT_URL', 'http://localhost:6333')
    monkeypatch.setenv('RAG_QDRANT_COLLECTION', 'documents')
    monkeypatch.delenv('RAG_DENSE_MODEL', raising=False)
    monkeypatch.setenv('RAG_SPARSE_MODEL', 'Qdrant/bm25')
    monkeypatch.setenv('RAG_EMBEDDING_PROVIDER', 'openai_compatible')
    monkeypatch.setenv('RAG_EMBEDDING_BASE_URL', 'http://localhost:8000')
    monkeypatch.setenv('RAG_EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-4B')
    monkeypatch.setenv('RAG_RERANKER_PROVIDER', 'http_qwen')
    monkeypatch.setenv('RAG_RERANKER_BASE_URL', 'http://localhost:8090')
    monkeypatch.setenv('RAG_RERANKER_MODEL', 'Qwen/Qwen3-Reranker-0.6B')

    builder = RecordingBuilder()

    backend = create_backend_from_env(builder=builder)

    assert isinstance(backend, FakeBackend)
    assert builder.calls == [
        {
            'qdrant_url': 'http://localhost:6333',
            'collection_name': 'documents',
            'dense_model': None,
            'sparse_model': 'Qdrant/bm25',
            'cache_dir': None,
            'threads': None,
            'embedding_provider': 'openai_compatible',
            'embedding_base_url': 'http://localhost:8000',
            'embedding_model': 'Qwen/Qwen3-Embedding-4B',
            'reranker_provider': 'http_qwen',
            'reranker_base_url': 'http://localhost:8090',
            'reranker_model': 'Qwen/Qwen3-Reranker-0.6B',
        }
    ]


def test_resolve_backend_options_from_env_exposes_optional_embedding_and_reranker_settings(monkeypatch):
    monkeypatch.setenv('RAG_EMBEDDING_PROVIDER', 'openai_compatible')
    monkeypatch.setenv('RAG_EMBEDDING_BASE_URL', 'http://localhost:8000')
    monkeypatch.setenv('RAG_EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-0.6B')
    monkeypatch.setenv('RAG_RERANKER_PROVIDER', 'http_qwen')
    monkeypatch.setenv('RAG_RERANKER_BASE_URL', 'http://localhost:8090')
    monkeypatch.setenv('RAG_RERANKER_MODEL', 'Qwen3-Reranker-0.6B')

    options = resolve_backend_options_from_env()

    assert options == {
        'embedding_provider': 'openai_compatible',
        'embedding_base_url': 'http://localhost:8000',
        'embedding_model': 'Qwen/Qwen3-Embedding-0.6B',
        'reranker_provider': 'http_qwen',
        'reranker_base_url': 'http://localhost:8090',
        'reranker_model': 'Qwen3-Reranker-0.6B',
    }
