from rag_ingest.document_encoders import StaticDocumentEncoder


def test_static_document_encoder_returns_dense_and_sparse_vectors_per_chunk():
    encoder = StaticDocumentEncoder(
        dense_vectors=[[0.1, 0.2]],
        sparse_vectors=[{'indices': [1], 'values': [0.8]}],
    )
    encoded = encoder.encode_chunks(['reset password policy'])
    assert encoded[0]['dense'] == [0.1, 0.2]
    assert encoded[0]['sparse']['indices'] == [1]
