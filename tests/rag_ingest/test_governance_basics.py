import os
import tempfile

from rag_ingest.config import get_retention_days
from rag_ingest.logging_utils import build_log_event
from rag_ingest.retry_utils import retry_operation
from rag_ingest.orphan_check import find_orphan_point_ids


def test_retention_days_comes_from_env_with_default():
    old = os.environ.pop('RAG_RETENTION_DAYS', None)
    try:
        assert get_retention_days() == 7
        os.environ['RAG_RETENTION_DAYS'] = '14'
        assert get_retention_days() == 14
    finally:
        if old is not None:
            os.environ['RAG_RETENTION_DAYS'] = old
        elif 'RAG_RETENTION_DAYS' in os.environ:
            del os.environ['RAG_RETENTION_DAYS']


def test_build_log_event_includes_required_fields():
    event = build_log_event('ingest_completed', document_key='doc-1', version_id='ver-1', status='ok')
    assert event['event'] == 'ingest_completed'
    assert event['document_key'] == 'doc-1'
    assert event['version_id'] == 'ver-1'
    assert event['status'] == 'ok'


def test_retry_operation_succeeds_after_retries():
    attempts = {'n': 0}

    def flaky():
        attempts['n'] += 1
        if attempts['n'] < 3:
            raise ValueError('temporary')
        return 'ok'

    result = retry_operation(flaky, retries=3)
    assert result == 'ok'
    assert attempts['n'] == 3


def test_find_orphan_point_ids_returns_points_missing_from_db_records():
    db_point_ids = set(['p1', 'p2'])
    qdrant_point_ids = set(['p1', 'p2', 'p3'])
    orphans = find_orphan_point_ids(db_point_ids, qdrant_point_ids)
    assert orphans == ['p3']
