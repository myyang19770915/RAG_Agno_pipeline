from rag_ingest.services.ingest_pipeline import ingest_document, FakeQdrant
from rag_ingest.db.session import InMemorySession
from rag_ingest.qdrant_payloads import build_qdrant_point_id


def test_new_version_writes_new_points_and_marks_old_version_inactive():
    qdrant = FakeQdrant()
    session = InMemorySession()
    metadata_v1 = {'document_key': 'sharepoint:SOP-001', 'version_fingerprint': 'fp1', 'source_system': 'sharepoint'}
    metadata_v2 = {'document_key': 'sharepoint:SOP-001', 'version_fingerprint': 'fp2', 'source_system': 'sharepoint'}

    first = ingest_document(session, qdrant, metadata_v1, ['a', 'b'], [[0.1], [0.2]])
    old_version_id = first['version'].version_id
    second = ingest_document(session, qdrant, metadata_v2, ['c'], [[0.3]])
    new_version_id = second['version'].version_id

    old_payload = qdrant.points[build_qdrant_point_id(old_version_id, 0)]['payload']
    new_payload = qdrant.points[build_qdrant_point_id(new_version_id, 0)]['payload']
    assert old_payload['chunk_id'] == '%s:0000' % old_version_id
    assert new_payload['chunk_id'] == '%s:0000' % new_version_id
    assert old_payload['is_active'] is False
    assert new_payload['is_latest'] is True
