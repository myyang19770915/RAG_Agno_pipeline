from rag_ingest.config import get_retention_days
from rag_ingest.jobs.nightly_cleanup import cleanup_inactive_versions
from rag_ingest.jobs.reconcile_counts import reconcile_active_chunk_counts, reconcile_orphans
from rag_ingest.logging_utils import build_log_event
from rag_ingest.services.ingest_pipeline import ingest_document, FakeQdrant
from rag_ingest.db.session import InMemorySession
from datetime import datetime, timedelta


def test_cleanup_uses_configurable_retention():
    session = InMemorySession()
    qdrant = FakeQdrant()
    first = ingest_document(session, qdrant, {'document_key': 'doc1', 'version_fingerprint': 'a', 'source_system': 'fs'}, ['x'], [[1]])
    ingest_document(session, qdrant, {'document_key': 'doc1', 'version_fingerprint': 'b', 'source_system': 'fs'}, ['y'], [[2]])
    first['version'].ingested_at = datetime.utcnow() - timedelta(days=10)
    deleted = cleanup_inactive_versions(session, qdrant, retention_days=7)
    assert deleted == 1


def test_reconcile_orphans_reports_extra_qdrant_points():
    db_ids = set(['a'])
    qdrant_ids = set(['a', 'b'])
    result = reconcile_orphans(db_ids, qdrant_ids)
    assert result['orphans'] == ['b']


def test_log_event_can_capture_conflict_signal():
    event = build_log_event('business_id_conflict', document_key='doc1', conflict=True)
    assert event['conflict'] is True
