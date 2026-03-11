from rag_ingest.services.ingest_pipeline import ingest_document, FakeQdrant
from rag_ingest.db.session import InMemorySession
from rag_ingest.jobs.reconcile_counts import reconcile_active_chunk_counts


def test_reconcile_flags_mismatched_active_chunk_counts():
    qdrant = FakeQdrant()
    session = InMemorySession()
    result = ingest_document(session, qdrant, {'document_key': 'doc1', 'version_fingerprint': 'a', 'source_system': 'fs'}, ['x', 'y'], [[1], [2]])
    version_id = result['version'].version_id
    del qdrant.points['%s:0001' % version_id]
    reconcile = reconcile_active_chunk_counts(session, qdrant, version_id)
    assert reconcile.status == 'mismatch'
