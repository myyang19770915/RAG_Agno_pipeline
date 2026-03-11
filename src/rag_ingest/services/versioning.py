from rag_ingest.db.models import Document, DocumentVersion


class ClassificationResult(object):
    def __init__(self, action):
        self.action = action


def classify_document_event(existing_document, current_fingerprint, incoming_fingerprint):
    if not existing_document:
        return ClassificationResult('new_document')
    if current_fingerprint == incoming_fingerprint:
        return ClassificationResult('skip')
    return ClassificationResult('new_version')


def upsert_document_version(session, metadata):
    document = session.get_document_by_key(metadata['document_key'])
    current_version = None
    if document:
        current_version = session.get_current_version(document)

    result = classify_document_event(bool(document), getattr(current_version, 'version_fingerprint', None), metadata['version_fingerprint'])

    if result.action == 'skip':
        return {'action': 'skip', 'document': document, 'version': current_version, 'prior_version': current_version}

    prior_version = current_version
    if not document:
        document = Document(
            document_key=metadata['document_key'],
            source_system=metadata.get('source_system'),
            business_id=metadata.get('business_id'),
            normalized_path=metadata.get('normalized_path'),
            title=metadata.get('title'),
            doc_type=metadata.get('doc_type'),
        )
        session.add_document(document)
        version_no = 1
    else:
        version_no = current_version.version_no + 1
        if prior_version:
            prior_version.status = 'superseded'

    version = DocumentVersion(
        document_id=document.document_id,
        version_no=version_no,
        version_fingerprint=metadata['version_fingerprint'],
        file_hash=metadata.get('file_hash'),
        text_hash=metadata.get('text_hash'),
        file_size=metadata.get('file_size', 0),
        source_modified_at=metadata.get('source_modified_at'),
        status='active',
        chunk_count=metadata.get('chunk_count', 0),
        embedding_model=metadata.get('embedding_model'),
        embedding_version=metadata.get('embedding_version'),
    )
    session.add_version(version)
    document.current_version_id = version.version_id
    if hasattr(session, 'save_document'):
        session.save_document(document)
    if prior_version:
        prior_version.superseded_by_version_id = version.version_id
        if hasattr(session, 'save_version'):
            session.save_version(prior_version)
    if hasattr(session, 'save_version'):
        session.save_version(version)
    return {'action': result.action, 'document': document, 'version': version, 'prior_version': prior_version}
