from rag_ingest.qdrant_integration import collection_definition



def test_collection_definition_supports_dense_and_sparse_vectors():
    cfg = collection_definition(vector_size=384, collection_name='documents')
    assert 'vectors_config' in cfg
    assert 'sparse_vectors_config' in cfg
    assert 'dense' in cfg['vectors_config']
    assert 'sparse' in cfg['sparse_vectors_config']
