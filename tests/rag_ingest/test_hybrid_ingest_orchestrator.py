from rag_ingest.hybrid_ingest_orchestrator import prepare_hybrid_chunk_vectors
from rag_ingest.document_encoders import StaticDocumentEncoder


def test_prepare_hybrid_chunk_vectors_splits_dense_and_sparse_outputs_for_ingest():
    encoder = StaticDocumentEncoder(
        dense_vectors=[[0.1, 0.2]],
        sparse_vectors=[{'indices': [1], 'values': [0.8]}],
    )
    dense_vectors, sparse_vectors = prepare_hybrid_chunk_vectors(['reset password'], encoder)
    assert dense_vectors == [[0.1, 0.2]]
    assert sparse_vectors[0]['indices'] == [1]
