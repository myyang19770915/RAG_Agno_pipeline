import os

from rag_ingest.embedding_provider import select_embedding_provider
from rag_ingest.fastembed_adapters import FastEmbedAdapterConfig, FastEmbedRuntimeFactory
from rag_ingest.qdrant_integration import QdrantClientFactory
from rag_ingest.qdrant_retriever_backend import QdrantRetrieverBackend
from rag_ingest.query_encoders import EmbeddingProviderDenseEncoder, RuntimeQueryEncoder, SparseFastEmbedEncoder, SplitQueryEncoder
from rag_ingest.rerank import select_reranker_from_env


def _required_setting(name):
    value = os.environ.get(name)
    if value:
        return value
    return None


def resolve_backend_options_from_env():
    return {
        'embedding_provider': os.environ.get('RAG_EMBEDDING_PROVIDER', 'fastembed'),
        'embedding_base_url': os.environ.get('RAG_EMBEDDING_BASE_URL'),
        'embedding_model': os.environ.get('RAG_EMBEDDING_MODEL'),
        'reranker_provider': os.environ.get('RAG_RERANKER_PROVIDER', 'none'),
        'reranker_base_url': os.environ.get('RAG_RERANKER_BASE_URL'),
        'reranker_model': os.environ.get('RAG_RERANKER_MODEL'),
    }


def _build_query_encoder(
    *,
    embedding_provider,
    dense_model,
    sparse_model,
    cache_dir=None,
    threads=None,
):
    if embedding_provider == 'openai_compatible':
        try:
            from fastembed import SparseTextEmbedding
        except Exception as exc:
            raise RuntimeError('fastembed package not installed') from exc

        sparse_model_instance = FastEmbedRuntimeFactory._build_model(
            SparseTextEmbedding,
            model_name=sparse_model,
            cache_dir=cache_dir,
            threads=threads,
            stage='sparse',
        )
        return SplitQueryEncoder(
            dense_encoder=EmbeddingProviderDenseEncoder(select_embedding_provider()),
            sparse_encoder=SparseFastEmbedEncoder(sparse_model_instance),
        )

    runtime = FastEmbedRuntimeFactory().create(
        FastEmbedAdapterConfig(
            dense_model=dense_model,
            sparse_model=sparse_model,
            cache_dir=cache_dir,
            threads=threads,
        )
    )
    return RuntimeQueryEncoder(runtime)


def _default_backend_builder(
    *,
    qdrant_url,
    collection_name,
    dense_model,
    sparse_model,
    cache_dir=None,
    threads=None,
    embedding_provider='fastembed',
    embedding_base_url=None,
    embedding_model=None,
    reranker_provider='none',
    reranker_base_url=None,
    reranker_model=None,
):
    client = QdrantClientFactory(url=qdrant_url).create()
    return QdrantRetrieverBackend(
        client=client,
        collection_name=collection_name,
        query_encoder=_build_query_encoder(
            embedding_provider=embedding_provider,
            dense_model=dense_model,
            sparse_model=sparse_model,
            cache_dir=cache_dir,
            threads=threads,
        ),
        reranker=select_reranker_from_env(),
    )


def create_backend_from_env(builder=None):
    options = resolve_backend_options_from_env()
    settings = {
        'qdrant_url': _required_setting('RAG_QDRANT_URL'),
        'collection_name': _required_setting('RAG_QDRANT_COLLECTION'),
        'dense_model': _required_setting('RAG_DENSE_MODEL'),
        'sparse_model': _required_setting('RAG_SPARSE_MODEL'),
        'cache_dir': os.environ.get('RAG_FASTEMBED_CACHE_DIR'),
        'threads': None,
        'embedding_provider': options['embedding_provider'],
        'embedding_base_url': options['embedding_base_url'],
        'embedding_model': options['embedding_model'],
        'reranker_provider': options['reranker_provider'],
        'reranker_base_url': options['reranker_base_url'],
        'reranker_model': options['reranker_model'],
    }

    missing = [
        env_name
        for env_name, value in [
            ('RAG_QDRANT_URL', settings['qdrant_url']),
            ('RAG_QDRANT_COLLECTION', settings['collection_name']),
            ('RAG_SPARSE_MODEL', settings['sparse_model']),
        ]
        if not value
    ]
    if settings['embedding_provider'] == 'fastembed' and not settings['dense_model']:
        missing.append('RAG_DENSE_MODEL')
    if settings['embedding_provider'] == 'openai_compatible':
        for env_name, value in [
            ('RAG_EMBEDDING_BASE_URL', settings['embedding_base_url']),
            ('RAG_EMBEDDING_MODEL', settings['embedding_model']),
        ]:
            if not value:
                missing.append(env_name)

    if missing:
        raise RuntimeError('Missing required Agno backend settings: %s' % ', '.join(missing))

    threads = os.environ.get('RAG_FASTEMBED_THREADS')
    if threads:
        settings['threads'] = int(threads)

    backend_builder = builder or _default_backend_builder
    return backend_builder(**settings)
