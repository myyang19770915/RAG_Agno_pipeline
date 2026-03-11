from rag_ingest.services.versioning import upsert_document_version
from rag_ingest.qdrant_payloads import build_payload, build_qdrant_point_id


class FakeQdrant(object):
    def __init__(self):
        self.points = {}

    def upsert_point(self, point_id, vector, payload):
        self.points[point_id] = {'vector': vector, 'payload': payload}

    def mark_version_inactive(self, version_id):
        for point_id, point in self.points.items():
            if point['payload'].get('version_id') == version_id:
                point['payload']['is_latest'] = False
                point['payload']['is_active'] = False

    def delete_inactive_version(self, version_id):
        to_delete = []
        for point_id, point in self.points.items():
            payload = point['payload']
            if payload.get('version_id') == version_id and payload.get('is_active') is False:
                to_delete.append(point_id)
        for point_id in to_delete:
            del self.points[point_id]
        return len(to_delete)

    def count_version(self, version_id, active_only=False):
        count = 0
        for point in self.points.values():
            payload = point['payload']
            if payload.get('version_id') == version_id:
                if active_only and payload.get('is_active') is not True:
                    continue
                count += 1
        return count


def ingest_document(session, qdrant, metadata, chunks, vectors, sparse_vectors=None, job=None):
    result = upsert_document_version(session, metadata)
    if job is not None and result['action'] == 'skip':
        job.skipped_same_version += 1
        job.logs.append({'event': 'document_skipped', 'document_key': metadata.get('document_key')})
    if result['action'] == 'skip':
        return result

    document = result['document']
    version = result['version']
    prior_version = result.get('prior_version')

    if prior_version and prior_version.version_id != version.version_id:
        qdrant.mark_version_inactive(prior_version.version_id)

    for chunk_index, vector in enumerate(vectors):
        payload = build_payload(
            document_id=document.document_id,
            document_key=document.document_key,
            version_id=version.version_id,
            version_no=version.version_no,
            business_id=document.business_id,
            source_system=document.source_system,
            normalized_path=document.normalized_path,
            title=document.title,
            doc_type=document.doc_type,
            chunk_index=chunk_index,
            is_latest=True,
            is_active=True,
            file_hash=metadata.get('file_hash'),
            text_hash=metadata.get('text_hash'),
            embedding_model=metadata.get('embedding_model'),
            embedding_version=metadata.get('embedding_version'),
            source_modified_at=metadata.get('source_modified_at'),
            ingested_at='now',
            text=chunks[chunk_index],
        )
        point_id = build_qdrant_point_id(version.version_id, chunk_index)
        point_vector = vector
        if sparse_vectors is not None:
            point_vector = {'dense': vector, 'sparse': sparse_vectors[chunk_index]}
        qdrant.upsert_point(point_id, point_vector, payload)
    version.chunk_count = len(vectors)
    if hasattr(session, 'save_version'):
        session.save_version(version)
    if job is not None:
        if result['action'] == 'new_document':
            job.new_docs += 1
        elif result['action'] == 'new_version':
            job.new_versions += 1
        job.logs.append(
            {
                'event': 'document_ingested',
                'document_key': metadata.get('document_key'),
                'version_id': version.version_id,
                'action': result['action'],
                'chunk_count': len(vectors),
            }
        )
    return result
