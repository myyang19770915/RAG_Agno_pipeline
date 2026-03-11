from rag_ingest.qdrant_payloads import build_qdrant_point_id


def build_hybrid_point_struct(point_id, dense_vector, sparse_vector, payload):
    live_point_id = point_id
    version_id = payload.get('version_id')
    chunk_index = payload.get('chunk_index')
    if version_id is not None and chunk_index is not None:
        live_point_id = build_qdrant_point_id(version_id, chunk_index)
    return {
        'id': live_point_id,
        'vector': {
            'dense': dense_vector,
            'sparse': sparse_vector,
        },
        'payload': payload,
    }
