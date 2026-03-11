from datetime import datetime, timedelta

from rag_ingest.db.session import InMemorySession
from rag_ingest.services.ingest_pipeline import FakeQdrant, ingest_document
from rag_ingest.services.job_control import (
    create_ingestion_job,
    finish_ingestion_job,
    rerun_failed_documents,
)
from rag_ingest.alerts import find_stale_active_versions


def test_ingestion_job_logs_capture_document_events():
    session = InMemorySession()
    qdrant = FakeQdrant()
    job = create_ingestion_job(session, source_system='sharepoint', total_files=1)

    ingest_document(
        session,
        qdrant,
        {'document_key': 'sharepoint:SOP-001', 'version_fingerprint': 'fp1', 'source_system': 'sharepoint'},
        ['a'],
        [[0.1]],
        job=job,
    )
    finish_ingestion_job(session, job)

    events = [entry['event'] for entry in job.logs]
    assert 'job_started' in events
    assert 'document_ingested' in events
    assert 'job_finished' in events


def test_rerun_failed_documents_only_retries_failed_items():
    session = InMemorySession()
    qdrant = FakeQdrant()
    original_job = create_ingestion_job(session, source_system='sharepoint', total_files=2)
    original_job.failed_documents = [
        {
            'document_key': 'sharepoint:SOP-404',
            'version_fingerprint': 'fp404',
            'source_system': 'sharepoint',
            'error': 'network timeout',
        }
    ]
    finish_ingestion_job(session, original_job, status='partial_failed')

    rerun_job = rerun_failed_documents(
        session,
        qdrant,
        original_job.job_id,
        chunks_by_document={'sharepoint:SOP-404': ['fixed text']},
        vectors_by_document={'sharepoint:SOP-404': [[0.8]]},
    )

    assert rerun_job.rerun_of_job_id == original_job.job_id
    assert rerun_job.status == 'completed'
    assert rerun_job.failed_files == 0
    assert rerun_job.new_docs == 1


def test_find_stale_active_versions_flags_old_active_version():
    session = InMemorySession()
    qdrant = FakeQdrant()
    result = ingest_document(
        session,
        qdrant,
        {'document_key': 'sharepoint:SOP-001', 'version_fingerprint': 'fp1', 'source_system': 'sharepoint'},
        ['a'],
        [[0.1]],
    )
    version = result['version']
    version.ingested_at = datetime.utcnow() - timedelta(days=45)

    alerts = find_stale_active_versions(session, now=datetime.utcnow(), max_age_days=30)

    assert len(alerts) == 1
    assert alerts[0]['version_id'] == version.version_id
    assert alerts[0]['severity'] == 'warning'
