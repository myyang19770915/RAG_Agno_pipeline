from rag_ingest.fastembed_adapters import FastEmbedAdapterConfig, build_runtime_factory_spec


def test_build_runtime_factory_spec_includes_dense_and_sparse_model_names():
    cfg = FastEmbedAdapterConfig(
        dense_model='sentence-transformers/all-MiniLM-L6-v2',
        sparse_model='Qdrant/bm25',
    )
    spec = build_runtime_factory_spec(cfg)
    assert spec['dense_model'] == 'sentence-transformers/all-MiniLM-L6-v2'
    assert spec['sparse_model'] == 'Qdrant/bm25'
