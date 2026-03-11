import os

from rag_ingest.embedding_provider import DeterministicEmbeddingProvider, select_embedding_provider


def test_deterministic_provider_returns_fixed_dim_vectors():
    provider = DeterministicEmbeddingProvider(dims=4)
    vectors = provider.embed_texts(['hello', 'world'])
    assert len(vectors) == 2
    assert len(vectors[0]) == 4


def test_select_provider_falls_back_without_api_key():
    old = os.environ.pop('OPENAI_API_KEY', None)
    try:
        provider = select_embedding_provider()
        assert provider.name == 'deterministic-local'
    finally:
        if old is not None:
            os.environ['OPENAI_API_KEY'] = old
