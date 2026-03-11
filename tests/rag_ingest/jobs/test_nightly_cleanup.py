from datetime import datetime, timedelta
from rag_ingest.services.ingest_pipeline import ingest_document, FakeQdrant
from rag_ingest.db.session import InMemorySession
from rag_ingest.jobs.nightly_cleanup import cleanup_inactive_versions


def test_cleanup_deletes_inactive_points_older_than_retention():
    qdrant = FakeQdrant()
    session = InMemorySession()
    first = ingest_document(session, qdrant, {'document_key': 'doc1', 'version_fingerprint': 'a', 'source_system': 'fs'}, ['x'] * 10, [[1]] * 10)
    ingest_document(session, qdrant, {'document_key': 'doc1', 'version_fingerprint': 'b', 'source_system': 'fs'}, ['y'], [[2]])
    first['version'].ingested_at = datetime.utcnow() - timedelta(days=10)
    deleted_count = cleanup_inactive_versions(session, qdrant, retention_days=7)
    assert deleted_count == 10
