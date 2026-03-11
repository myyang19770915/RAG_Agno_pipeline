import base64
import os
import shutil
import tempfile

from rag_ingest.file_ingest import read_text_file, scan_files
from rag_ingest.local_folder_pipeline import process_folder_documents
from rag_ingest.db.sqlite_session import initialize_schema, SQLiteSession
from rag_ingest.services.ingest_pipeline import FakeQdrant

MINIMAL_PDF_BASE64 = b"JVBERi0xLjEKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAzMDAgMTQ0XSAvQ29udGVudHMgNCAwIFIgL1Jlc291cmNlcyA8PCAvRm9udCA8PCAvRjEgNSAwIFIgPj4gPj4gPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCA1OCA+PgpzdHJlYW0KQlQKL0YxIDI0IFRmCjcyIDEwMCBUZAoo5paH5Lu257eo6JmfOiBTT1AtMDAyKSBUagooUERGIGluZ2VzdCB3b3JrcykgVGoKRVQKZW5kc3RyZWFtCmVuZG9iago1IDAgb2JqCjw8IC9UeXBlIC9Gb250IC9TdWJ0eXBlIC9UeXBlMSAvQmFzZUZvbnQgL0hlbHZldGljYSA+PgplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDEwIDAwMDAwIG4gCjAwMDAwMDAwNjMgMDAwMDAgbiAKMDAwMDAwMDExOCAwMDAwMCBuIAowMDAwMDAwMjQ0IDAwMDAwIG4gCjAwMDAwMDAzNTIgMDAwMDAgbiAKdHJhaWxlcgo8PCAvUm9vdCAxIDAgUiAvU2l6ZSA2ID4+CnN0YXJ0eHJlZgo0MjIKJSVFT0YK"


def _write_pdf(path):
    with open(path, 'wb') as f:
        f.write(base64.b64decode(MINIMAL_PDF_BASE64))


def test_scan_files_includes_pdf():
    root = tempfile.mkdtemp(prefix='rag_pdf_')
    try:
        pdf_path = os.path.join(root, 'doc.pdf')
        _write_pdf(pdf_path)
        names = [os.path.basename(x) for x in scan_files(root)]
        assert 'doc.pdf' in names
    finally:
        shutil.rmtree(root)


def test_read_text_file_extracts_text_from_pdf():
    root = tempfile.mkdtemp(prefix='rag_pdf_')
    try:
        pdf_path = os.path.join(root, 'doc.pdf')
        _write_pdf(pdf_path)
        text = read_text_file(pdf_path)
        assert 'SOP-002' in text or 'PDF ingest works' in text
    finally:
        shutil.rmtree(root)


def test_process_folder_documents_accepts_pdf():
    root = tempfile.mkdtemp(prefix='rag_pdf_')
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    try:
        pdf_path = os.path.join(root, 'doc.pdf')
        _write_pdf(pdf_path)
        initialize_schema(db_path)
        session = SQLiteSession(db_path)
        qdrant = FakeQdrant()
        summary = process_folder_documents(root, session, qdrant, source_system='localfs', chunk_size=20, overlap=5)
        assert summary['processed'] == 1
        assert len(qdrant.points) >= 1
    finally:
        shutil.rmtree(root)
        os.remove(db_path)
