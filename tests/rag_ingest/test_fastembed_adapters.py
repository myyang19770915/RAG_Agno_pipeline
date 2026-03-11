from rag_ingest.fastembed_adapters import build_fastembed_config


def test_build_fastembed_config_keeps_dense_and_sparse_model_names():
    cfg = build_fastembed_config(
        dense_model='sentence-transformers/all-MiniLM-L6-v2',
        sparse_model='Qdrant/bm25',
    )
    assert cfg['dense_model'] == 'sentence-transformers/all-MiniLM-L6-v2'
    assert cfg['sparse_model'] == 'Qdrant/bm25'
