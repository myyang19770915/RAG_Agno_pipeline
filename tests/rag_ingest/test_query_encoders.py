from rag_ingest.query_encoders import EncodedQuery


def test_encoded_query_can_hold_dense_and_sparse_query_forms():
    encoded = EncodedQuery(
        text='reset password',
        dense=[0.1, 0.2],
        sparse={'indices': [3], 'values': [1.0]},
    )
    assert encoded.dense == [0.1, 0.2]
    assert encoded.sparse['indices'] == [3]
