import uuid
from datetime import datetime


class Document(object):
    def __init__(self, document_key=None, source_system=None, business_id=None, normalized_path=None, title=None, doc_type=None):
        self.document_id = str(uuid.uuid4())
        self.document_key = document_key
        self.source_system = source_system
        self.business_id = business_id
        self.normalized_path = normalized_path
        self.title = title
        self.doc_type = doc_type
        self.current_version_id = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class DocumentVersion(object):
    def __init__(self, document_id=None, version_no=1, version_fingerprint=None, file_hash=None, text_hash=None, file_size=0, source_modified_at=None, status='active', chunk_count=0, embedding_model=None, embedding_version=None):
        self.version_id = str(uuid.uuid4())
        self.document_id = document_id
        self.version_no = version_no
        self.version_fingerprint = version_fingerprint
        self.file_hash = file_hash
        self.text_hash = text_hash
        self.file_size = file_size
        self.source_modified_at = source_modified_at
        self.ingested_at = datetime.utcnow()
        self.status = status
        self.superseded_by_version_id = None
        self.chunk_count = chunk_count
        self.embedding_model = embedding_model
        self.embedding_version = embedding_version
        self.deleted_at = None


class IngestionJob(object):
    def __init__(self, source_system=None, total_files=0, rerun_of_job_id=None):
        self.job_id = str(uuid.uuid4())
        self.source_system = source_system
        self.started_at = datetime.utcnow()
        self.finished_at = None
        self.status = 'running'
        self.total_files = total_files
        self.new_docs = 0
        self.new_versions = 0
        self.skipped_same_version = 0
        self.failed_files = 0
        self.notes = None
        self.logs = []
        self.failed_documents = []
        self.rerun_of_job_id = rerun_of_job_id
