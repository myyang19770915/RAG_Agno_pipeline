from rag_ingest.db.models import Document, DocumentVersion


def test_document_has_current_version_field():
    assert hasattr(Document(), 'current_version_id')


def test_document_version_has_status_field():
    assert hasattr(DocumentVersion(), 'status')
