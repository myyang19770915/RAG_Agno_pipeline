import os
import tempfile
import sqlite3

from rag_ingest.db.models import Document, DocumentVersion
from rag_ingest.db.sqlite_session import SQLiteSession, initialize_schema
from rag_ingest.services.versioning import upsert_document_version


def make_db_path():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return path


def test_initialize_schema_creates_required_tables():
    db_path = make_db_path()
    try:
        initialize_schema(db_path)
        conn = sqlite3.connect(db_path)
        names = set([row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")])
        assert 'documents' in names
        assert 'document_versions' in names
        assert 'ingestion_jobs' in names
        conn.close()
    finally:
        os.remove(db_path)


def test_sqlite_session_persists_document_and_version():
    db_path = make_db_path()
    try:
        initialize_schema(db_path)
        session = SQLiteSession(db_path)
        result = upsert_document_version(session, {
            'document_key': 'sharepoint:SOP-001',
            'version_fingerprint': 'fp1',
            'source_system': 'sharepoint',
            'business_id': 'SOP-001',
            'normalized_path': '/qa/sop-001.pdf',
            'title': 'SOP 001',
            'doc_type': 'pdf',
        })
        session2 = SQLiteSession(db_path)
        doc = session2.get_document_by_key('sharepoint:SOP-001')
        current = session2.get_current_version(doc)
        assert doc.business_id == 'SOP-001'
        assert current.version_fingerprint == 'fp1'
        assert result['action'] == 'new_document'
    finally:
        os.remove(db_path)


def test_sqlite_session_marks_prior_version_superseded():
    db_path = make_db_path()
    try:
        initialize_schema(db_path)
        session = SQLiteSession(db_path)
        upsert_document_version(session, {'document_key': 'doc1', 'version_fingerprint': 'v1', 'source_system': 'fs'})
        result = upsert_document_version(session, {'document_key': 'doc1', 'version_fingerprint': 'v2', 'source_system': 'fs'})
        versions = session.get_versions_for_document(result['document'].document_id)
        statuses = sorted([v.status for v in versions])
        assert statuses == ['active', 'superseded']
    finally:
        os.remove(db_path)


def test_sqlite_session_rolls_back_failed_transaction():
    db_path = make_db_path()
    try:
        initialize_schema(db_path)
        session = SQLiteSession(db_path)
        doc = Document(document_key='docx', source_system='fs')
        session.add_document(doc)
        duplicate = Document(document_key='docx', source_system='fs')
        try:
            session.add_document(duplicate)
            assert False, 'expected integrity error'
        except Exception:
            pass
        session2 = SQLiteSession(db_path)
        assert session2.get_document_by_key('docx') is not None
        versions = session2.get_versions_for_document(doc.document_id)
        assert versions == []
    finally:
        os.remove(db_path)
