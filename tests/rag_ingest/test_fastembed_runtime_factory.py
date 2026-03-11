import pytest

from rag_ingest.fastembed_adapters import (
    FastEmbedAdapterConfig,
    FastEmbedRuntimeFactory,
)


class FakeDenseModel:
    def __init__(self, model_name=None, cache_dir=None, threads=None, **kwargs):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.threads = threads
        self.kwargs = kwargs


class FakeSparseModel:
    def __init__(self, model_name=None, cache_dir=None, threads=None, **kwargs):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.threads = threads
        self.kwargs = kwargs


class BrokenDenseModel:
    def __init__(self, *args, **kwargs):
        raise RuntimeError('boom')


def test_runtime_factory_builds_dense_and_sparse_models_from_config():
    cfg = FastEmbedAdapterConfig(
        dense_model='BAAI/bge-small-en-v1.5',
        sparse_model='Qdrant/bm25',
        cache_dir='/tmp/fastembed-cache',
        threads=2,
    )

    runtime = FastEmbedRuntimeFactory(
        dense_model_cls=FakeDenseModel,
        sparse_model_cls=FakeSparseModel,
    ).create(cfg)

    assert runtime.dense_model.model_name == 'BAAI/bge-small-en-v1.5'
    assert runtime.sparse_model.model_name == 'Qdrant/bm25'
    assert runtime.dense_model.cache_dir == '/tmp/fastembed-cache'
    assert runtime.sparse_model.threads == 2


def test_runtime_factory_rejects_missing_model_names():
    cfg = FastEmbedAdapterConfig(dense_model=None, sparse_model='Qdrant/bm25')

    with pytest.raises(ValueError, match='dense_model'):
        FastEmbedRuntimeFactory(
            dense_model_cls=FakeDenseModel,
            sparse_model_cls=FakeSparseModel,
        ).create(cfg)


def test_runtime_factory_surfaces_dense_initialization_failure_with_context():
    cfg = FastEmbedAdapterConfig(
        dense_model='bad-dense',
        sparse_model='Qdrant/bm25',
    )

    with pytest.raises(RuntimeError, match='Failed to initialize FastEmbed dense model'):
        FastEmbedRuntimeFactory(
            dense_model_cls=BrokenDenseModel,
            sparse_model_cls=FakeSparseModel,
        ).create(cfg)
