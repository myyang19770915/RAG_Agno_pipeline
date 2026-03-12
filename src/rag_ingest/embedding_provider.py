import hashlib
import os

from rag_ingest.http_embedding_adapter import HttpEmbeddingAdapter


def _optional_timeout(name, default=10):
    value = os.environ.get(name)
    if value in (None, ''):
        return default
    return float(value)


class DeterministicEmbeddingProvider(object):
    name = 'deterministic-local'

    def __init__(self, dims=4):
        self.dims = dims

    def embed_texts(self, texts):
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode('utf-8')).digest()
            values = []
            for i in range(self.dims):
                values.append((digest[i] % 100) / 100.0)
            vectors.append(values)
        return vectors


class OpenAICompatibleEmbeddingProvider(object):
    name = 'openai-compatible'

    def __init__(self, model='text-embedding-3-small', base_url=None, api_key=None):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key

    def embed_texts(self, texts):
        try:
            from openai import OpenAI
        except Exception:
            raise RuntimeError('openai package not installed')
        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        response = client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


def select_embedding_provider():
    provider_name = os.environ.get('RAG_EMBEDDING_PROVIDER')
    if provider_name == 'openai_compatible':
        return HttpEmbeddingAdapter(
            base_url=os.environ.get('RAG_EMBEDDING_BASE_URL', os.environ.get('OPENAI_BASE_URL', 'http://127.0.0.1:8000')),
            model=os.environ.get('RAG_EMBEDDING_MODEL', os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')),
            api_key=os.environ.get('OPENAI_API_KEY') or None,
            timeout_seconds=_optional_timeout('RAG_EMBEDDING_TIMEOUT_SECONDS'),
        )

    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        return OpenAICompatibleEmbeddingProvider(
            model=os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small'),
            base_url=os.environ.get('OPENAI_BASE_URL'),
            api_key=api_key,
        )
    return DeterministicEmbeddingProvider(dims=int(os.environ.get('DETERMINISTIC_EMBED_DIMS', '4')))
