from rag_ingest.db.models import Document, DocumentVersion


class InMemorySession(object):
    def __init__(self):
        self.documents = []
        self.versions = []
        self.jobs = []

    def add_document(self, document):
        self.documents.append(document)
        return document

    def add_version(self, version):
        self.versions.append(version)
        return version

    def get_document_by_key(self, document_key):
        for doc in self.documents:
            if doc.document_key == document_key:
                return doc
        return None

    def get_versions_for_document(self, document_id):
        return [v for v in self.versions if v.document_id == document_id]

    def get_current_version(self, document):
        for version in self.versions:
            if version.version_id == document.current_version_id:
                return version
        return None

    def add_job(self, job):
        self.jobs.append(job)
        return job

    def get_job(self, job_id):
        for job in self.jobs:
            if job.job_id == job_id:
                return job
        return None
