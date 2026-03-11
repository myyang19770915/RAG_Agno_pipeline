from rag_ingest.qdrant_hybrid_live_ops import build_hybrid_point_struct
from rag_ingest.qdrant_payloads import build_payload, build_qdrant_point_id


def test_build_hybrid_point_struct_uses_qdrant_safe_live_id_and_preserves_logical_chunk_id_in_payload():
    payload = build_payload(
        document_id='doc1',
        document_key='sharepoint:SOP-001',
        version_id='v1',
        version_no=1,
        chunk_index=0,
        is_latest=True,
        is_active=True,
    )

    point = build_hybrid_point_struct(
        point_id='v1:0000',
        dense_vector=[0.1, 0.2],
        sparse_vector={'indices': [1], 'values': [0.7]},
        payload=payload,
    )

    assert point['id'] == build_qdrant_point_id('v1', 0)
    assert point['id'] != payload['chunk_id']
    assert payload['chunk_id'] == 'v1:0000'
    assert point['payload']['chunk_id'] == 'v1:0000'
    assert point['vector']['dense'] == [0.1, 0.2]
    assert point['vector']['sparse']['indices'] == [1]
