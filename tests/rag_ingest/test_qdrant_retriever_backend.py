from rag_ingest.qdrant_retriever_backend import normalize_qdrant_result


def test_normalize_qdrant_result_maps_payload_to_retriever_candidate():
    candidate = normalize_qdrant_result(
        {
            'id': 'v1:0000',
            'score': 0.88,
            'payload': {
                'text': 'reset password policy steps',
                'document_key': 'doc1',
                'version_id': 'v1',
                'is_latest': True,
                'is_active': True,
            },
        }
    )
    assert candidate['chunk_id'] == 'v1:0000'
    assert candidate['document_key'] == 'doc1'
    assert candidate['version_id'] == 'v1'
