from rag_ingest.sparse_vectors import build_sparse_vector


def test_build_sparse_vector_returns_indices_and_values_shape():
    sparse = build_sparse_vector(indices=[1, 7, 9], values=[0.3, 0.9, 0.2])
    assert sparse == {'indices': [1, 7, 9], 'values': [0.3, 0.9, 0.2]}
