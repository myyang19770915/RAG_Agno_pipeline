from rag_ingest.services.ingest_pipeline import ingest_document, FakeQdrant
from rag_ingest.db.session import InMemorySession
from rag_ingest.qdrant_payloads import build_qdrant_point_id


def test_ingest_document_writes_dense_and_sparse_vectors_when_provided():
    qdrant = FakeQdrant()
    session = InMemorySession()

    result = ingest_document(
        session,
        qdrant,
        {'document_key': 'doc1', 'version_fingerprint': 'fp1', 'source_system': 'fs'},
        ['reset password policy'],
        [[0.1, 0.2]],
        sparse_vectors=[{'indices': [1, 5], 'values': [0.4, 0.9]}],
    )

    point = qdrant.points[build_qdrant_point_id(result['version'].version_id, 0)]
    assert point['payload']['chunk_id'] == f"{result['version'].version_id}:0000"
    assert point['vector']['dense'] == [0.1, 0.2]
    assert point['vector']['sparse']['indices'] == [1, 5]
