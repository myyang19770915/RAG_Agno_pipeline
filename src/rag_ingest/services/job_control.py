from datetime import datetime

from rag_ingest.db.models import IngestionJob
from rag_ingest.logging_utils import build_log_event
from rag_ingest.services.ingest_pipeline import ingest_document


def append_job_log(job, event, **kwargs):
    job.logs.append(build_log_event(event, **kwargs))


def create_ingestion_job(session, source_system, total_files=0, rerun_of_job_id=None):
    job = IngestionJob(source_system=source_system, total_files=total_files, rerun_of_job_id=rerun_of_job_id)
    session.add_job(job)
    append_job_log(job, 'job_started', source_system=source_system, total_files=total_files)
    return job


def finish_ingestion_job(session, job, status='completed'):
    job.status = status
    job.finished_at = datetime.utcnow()
    append_job_log(job, 'job_finished', status=status)
    return job


def rerun_failed_documents(session, qdrant, original_job_id, chunks_by_document, vectors_by_document):
    original_job = session.get_job(original_job_id)
    if not original_job:
        raise ValueError('original job not found')

    rerun_job = create_ingestion_job(
        session,
        source_system=original_job.source_system,
        total_files=len(original_job.failed_documents),
        rerun_of_job_id=original_job.job_id,
    )

    for failed in original_job.failed_documents:
        document_key = failed['document_key']
        metadata = dict(failed)
        metadata.pop('error', None)
        ingest_document(
            session,
            qdrant,
            metadata,
            chunks_by_document[document_key],
            vectors_by_document[document_key],
            job=rerun_job,
        )

    finish_ingestion_job(session, rerun_job, status='completed')
    return rerun_job
