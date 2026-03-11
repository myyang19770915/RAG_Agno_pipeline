from rag_ingest.services.versioning import classify_document_event, upsert_document_version
from rag_ingest.db.session import InMemorySession


def test_same_document_same_fingerprint_skips():
    result = classify_document_event(existing_document=True, current_fingerprint='abc', incoming_fingerprint='abc')
    assert result.action == 'skip'


def test_same_document_new_fingerprint_creates_new_version():
    result = classify_document_event(existing_document=True, current_fingerprint='abc', incoming_fingerprint='xyz')
    assert result.action == 'new_version'


def test_new_document_creates_document():
    result = classify_document_event(existing_document=False, current_fingerprint=None, incoming_fingerprint='xyz')
    assert result.action == 'new_document'


def test_upsert_document_version_marks_previous_version_superseded():
    session = InMemorySession()
    first = {
        'document_key': 'sharepoint:SOP-001',
        'version_fingerprint': 'fp1',
        'source_system': 'sharepoint',
    }
    second = {
        'document_key': 'sharepoint:SOP-001',
        'version_fingerprint': 'fp2',
        'source_system': 'sharepoint',
    }
    first_result = upsert_document_version(session, first)
    second_result = upsert_document_version(session, second)
    assert first_result['version'].status == 'superseded'
    assert second_result['version'].status == 'active'
