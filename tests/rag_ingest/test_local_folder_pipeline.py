import os
import shutil
import tempfile

from rag_ingest.local_folder_pipeline import process_folder_documents
from rag_ingest.db.sqlite_session import initialize_schema, SQLiteSession
from rag_ingest.services.ingest_pipeline import FakeQdrant


def test_process_folder_documents_builds_versioned_chunks_from_real_files():
    root = tempfile.mkdtemp(prefix='rag_folder_')
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    try:
        with open(os.path.join(root, 'doc1.md'), 'w') as f:
            f.write('文件編號: SOP-001\nhello world ' * 20)
        initialize_schema(db_path)
        session = SQLiteSession(db_path)
        qdrant = FakeQdrant()
        summary = process_folder_documents(root, session, qdrant, source_system='localfs', chunk_size=20, overlap=5)
        doc = session.get_document_by_key('localfs:SOP-001')
        current = session.get_current_version(doc)
        assert summary['processed'] == 1
        assert doc is not None
        assert current.chunk_count > 0
        assert len(qdrant.points) == current.chunk_count
    finally:
        shutil.rmtree(root)
        os.remove(db_path)
