import os
import pytest

from rag_ingest.embedding_provider import OpenAICompatibleEmbeddingProvider


@pytest.mark.skipif(not os.environ.get('OPENAI_API_KEY'), reason='OPENAI_API_KEY not set')
def test_openai_small_embedding_live():
    provider = OpenAICompatibleEmbeddingProvider(
        model=os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small'),
        base_url=os.environ.get('OPENAI_BASE_URL'),
        api_key=os.environ['OPENAI_API_KEY'],
    )
    vectors = provider.embed_texts(['hello world'])
    assert len(vectors) == 1
    assert len(vectors[0]) > 100
