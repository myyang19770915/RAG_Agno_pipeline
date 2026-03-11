from rag_ingest.query_encoders import StaticQueryEncoder


def test_static_query_encoder_returns_dense_and_sparse_shapes():
    encoder = StaticQueryEncoder(
        dense_vector=[0.1, 0.2],
        sparse_vector={'indices': [3], 'values': [1.0]},
    )
    encoded = encoder.encode('reset password')
    assert encoded.text == 'reset password'
    assert encoded.dense == [0.1, 0.2]
    assert encoded.sparse['indices'] == [3]
