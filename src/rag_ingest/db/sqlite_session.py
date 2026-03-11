import sqlite3

from rag_ingest.db.models import Document, DocumentVersion


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    document_key TEXT UNIQUE NOT NULL,
    source_system TEXT,
    business_id TEXT,
    normalized_path TEXT,
    title TEXT,
    doc_type TEXT,
    current_version_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS document_versions (
    version_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    version_no INTEGER NOT NULL,
    version_fingerprint TEXT NOT NULL,
    file_hash TEXT,
    text_hash TEXT,
    file_size INTEGER,
    source_modified_at TEXT,
    ingested_at TEXT,
    status TEXT,
    superseded_by_version_id TEXT,
    chunk_count INTEGER,
    embedding_model TEXT,
    embedding_version TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id TEXT PRIMARY KEY,
    source_system TEXT,
    started_at TEXT,
    finished_at TEXT,
    status TEXT,
    total_files INTEGER,
    new_docs INTEGER,
    new_versions INTEGER,
    skipped_same_version INTEGER,
    failed_files INTEGER,
    notes TEXT
);
"""


def initialize_schema(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def _row_to_document(row):
    if not row:
        return None
    doc = Document(
        document_key=row[1],
        source_system=row[2],
        business_id=row[3],
        normalized_path=row[4],
        title=row[5],
        doc_type=row[6],
    )
    doc.document_id = row[0]
    doc.current_version_id = row[7]
    doc.created_at = row[8]
    doc.updated_at = row[9]
    return doc


def _row_to_version(row):
    if not row:
        return None
    version = DocumentVersion(
        document_id=row[1],
        version_no=row[2],
        version_fingerprint=row[3],
        file_hash=row[4],
        text_hash=row[5],
        file_size=row[6],
        source_modified_at=row[7],
        status=row[9],
        chunk_count=row[11] or 0,
        embedding_model=row[12],
        embedding_version=row[13],
    )
    version.version_id = row[0]
    version.ingested_at = row[8]
    version.superseded_by_version_id = row[10]
    version.deleted_at = row[14]
    return version


class SQLiteSession(object):
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def add_document(self, document):
        try:
            self.conn.execute(
                "INSERT INTO documents (document_id, document_key, source_system, business_id, normalized_path, title, doc_type, current_version_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    document.document_id,
                    document.document_key,
                    document.source_system,
                    document.business_id,
                    document.normalized_path,
                    document.title,
                    document.doc_type,
                    document.current_version_id,
                    str(document.created_at),
                    str(document.updated_at),
                ),
            )
            self.conn.commit()
            return document
        except Exception:
            self.conn.rollback()
            raise

    def add_version(self, version):
        try:
            self.conn.execute(
                "INSERT INTO document_versions (version_id, document_id, version_no, version_fingerprint, file_hash, text_hash, file_size, source_modified_at, ingested_at, status, superseded_by_version_id, chunk_count, embedding_model, embedding_version, deleted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    version.version_id,
                    version.document_id,
                    version.version_no,
                    version.version_fingerprint,
                    version.file_hash,
                    version.text_hash,
                    version.file_size,
                    version.source_modified_at,
                    str(version.ingested_at),
                    version.status,
                    version.superseded_by_version_id,
                    version.chunk_count,
                    version.embedding_model,
                    version.embedding_version,
                    version.deleted_at,
                ),
            )
            self.conn.commit()
            return version
        except Exception:
            self.conn.rollback()
            raise

    def save_document(self, document):
        self.conn.execute(
            "UPDATE documents SET current_version_id = ?, updated_at = ? WHERE document_id = ?",
            (document.current_version_id, str(document.updated_at), document.document_id),
        )
        self.conn.commit()
        return document

    def save_version(self, version):
        self.conn.execute(
            "UPDATE document_versions SET status = ?, superseded_by_version_id = ?, chunk_count = ?, deleted_at = ? WHERE version_id = ?",
            (version.status, version.superseded_by_version_id, version.chunk_count, version.deleted_at, version.version_id),
        )
        self.conn.commit()
        return version

    def get_document_by_key(self, document_key):
        cur = self.conn.execute("SELECT * FROM documents WHERE document_key = ?", (document_key,))
        return _row_to_document(cur.fetchone())

    def get_versions_for_document(self, document_id):
        cur = self.conn.execute("SELECT * FROM document_versions WHERE document_id = ? ORDER BY version_no", (document_id,))
        return [_row_to_version(r) for r in cur.fetchall()]

    def get_current_version(self, document):
        if not document or not document.current_version_id:
            return None
        cur = self.conn.execute("SELECT * FROM document_versions WHERE version_id = ?", (document.current_version_id,))
        return _row_to_version(cur.fetchone())
