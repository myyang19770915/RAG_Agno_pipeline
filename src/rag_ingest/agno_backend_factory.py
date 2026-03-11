import os

from rag_ingest.fastembed_adapters import FastEmbedAdapterConfig, FastEmbedRuntimeFactory
from rag_ingest.qdrant_integration import QdrantClientFactory
from rag_ingest.qdrant_retriever_backend import QdrantRetrieverBackend
from rag_ingest.query_encoders import RuntimeQueryEncoder


def _required_setting(name):
    value = os.environ.get(name)
    if value:
        return value
    return None


def _default_backend_builder(
    *,
    qdrant_url,
    collection_name,
    dense_model,
    sparse_model,
    cache_dir=None,
    threads=None,
):
    runtime = FastEmbedRuntimeFactory().create(
        FastEmbedAdapterConfig(
            dense_model=dense_model,
            sparse_model=sparse_model,
            cache_dir=cache_dir,
            threads=threads,
        )
    )
    client = QdrantClientFactory(url=qdrant_url).create()
    return QdrantRetrieverBackend(
        client=client,
        collection_name=collection_name,
        query_encoder=RuntimeQueryEncoder(runtime),
    )


def create_backend_from_env(builder=None):
    settings = {
        'qdrant_url': _required_setting('RAG_QDRANT_URL'),
        'collection_name': _required_setting('RAG_QDRANT_COLLECTION'),
        'dense_model': _required_setting('RAG_DENSE_MODEL'),
        'sparse_model': _required_setting('RAG_SPARSE_MODEL'),
        'cache_dir': os.environ.get('RAG_FASTEMBED_CACHE_DIR'),
        'threads': None,
    }

    missing = [
        env_name
        for env_name, value in [
            ('RAG_QDRANT_URL', settings['qdrant_url']),
            ('RAG_QDRANT_COLLECTION', settings['collection_name']),
            ('RAG_DENSE_MODEL', settings['dense_model']),
            ('RAG_SPARSE_MODEL', settings['sparse_model']),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError('Missing required Agno backend settings: %s' % ', '.join(missing))

    threads = os.environ.get('RAG_FASTEMBED_THREADS')
    if threads:
        settings['threads'] = int(threads)

    backend_builder = builder or _default_backend_builder
    return backend_builder(**settings)
