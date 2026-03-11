import pytest

from rag_ingest.agno_backend_factory import create_backend_from_env


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
        }
    ]
