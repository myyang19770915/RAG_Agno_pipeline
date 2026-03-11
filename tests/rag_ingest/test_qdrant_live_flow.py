from qdrant_client import models

from rag_ingest.qdrant_integration import QdrantClientFactory
from rag_ingest.qdrant_live_ops import LiveQdrantOps
from rag_ingest.qdrant_payloads import build_payload, build_qdrant_point_id


def test_live_qdrant_upsert_mark_inactive_and_delete_flow():
    client = QdrantClientFactory(url='http://localhost:6333').create()
    collection_name = 'documents_live_flow'
    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        client.delete_collection(collection_name)

    ops = LiveQdrantOps(client, collection_name=collection_name)
    ops.ensure_collection(vector_size=4)

    version_id = 'ver_live_001'
    payload = build_payload(
        document_id='doc_1',
        document_key='sharepoint:SOP-001',
        version_id=version_id,
        version_no=1,
        business_id='SOP-001',
        source_system='sharepoint',
        normalized_path='/qa/sop-001.pdf',
        title='SOP 001',
        doc_type='pdf',
        chunk_index=0,
        file_hash='fh1',
        text_hash='th1',
        embedding_model='test-model',
        embedding_version='v1',
        source_modified_at='2026-03-11T12:00:00Z',
        ingested_at='2026-03-11T12:00:00Z',
        is_latest=True,
        is_active=True,
    )
    point = models.PointStruct(id=build_qdrant_point_id(version_id, 0), vector=[0.1, 0.2, 0.3, 0.4], payload=payload)
    ops.upsert_points([point])

    result = ops.query_latest([0.1, 0.2, 0.3, 0.4], limit=3)
    assert len(result.points) >= 1

    ops.mark_old_version_inactive(version_id)
    result_after_inactive = client.query_points(
        collection_name=collection_name,
        query=[0.1, 0.2, 0.3, 0.4],
        limit=3,
        with_payload=True,
        query_filter=ops.latest_filter(),
    )
    assert len(result_after_inactive.points) == 0

    ops.delete_inactive_version(version_id)
    scroll_result = client.scroll(collection_name=collection_name, limit=10, with_payload=True)
    assert len(scroll_result[0]) == 0


def test_live_qdrant_same_point_id_upsert_does_not_duplicate():
    client = QdrantClientFactory(url='http://localhost:6333').create()
    collection_name = 'documents_live_dedupe'
    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        client.delete_collection(collection_name)

    ops = LiveQdrantOps(client, collection_name=collection_name)
    ops.ensure_collection(vector_size=4)

    version_id = 'ver_dup_001'
    point_id = build_qdrant_point_id(version_id, 0)
    payload = build_payload(
        document_id='doc_1',
        document_key='sharepoint:SOP-001',
        version_id=version_id,
        version_no=1,
        business_id='SOP-001',
        source_system='sharepoint',
        normalized_path='/qa/sop-001.pdf',
        title='SOP 001',
        doc_type='pdf',
        chunk_index=0,
        file_hash='fh1',
        text_hash='th1',
        embedding_model='test-model',
        embedding_version='v1',
        source_modified_at='2026-03-11T12:00:00Z',
        ingested_at='2026-03-11T12:00:00Z',
        is_latest=True,
        is_active=True,
    )
    point1 = models.PointStruct(id=point_id, vector=[0.1, 0.2, 0.3, 0.4], payload=payload)
    point2 = models.PointStruct(id=point_id, vector=[0.2, 0.3, 0.4, 0.5], payload=payload)

    ops.upsert_points([point1])
    ops.upsert_points([point2])

    scroll_result = client.scroll(collection_name=collection_name, limit=10, with_payload=True)
    assert len(scroll_result[0]) == 1
