from rag_ingest.qdrant_integration import QdrantClientFactory


def test_live_qdrant_create_collection_and_indexes():
    client = QdrantClientFactory(url='http://localhost:6333').create()
    collection_name = 'documents_test'
    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config={'size': 4, 'distance': 'Cosine'},
    )
    client.create_payload_index(collection_name, 'document_key', 'keyword')
    client.create_payload_index(collection_name, 'version_id', 'keyword')
    client.create_payload_index(collection_name, 'is_latest', 'bool')
    client.create_payload_index(collection_name, 'is_active', 'bool')

    collections = [c.name for c in client.get_collections().collections]
    assert collection_name in collections
