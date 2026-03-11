from rag_ingest.live_smoke import build_smoke_payload, run_live_smoke


class StubDocumentEncoder:
    def encode_chunks(self, chunks):
        return [
            {
                'dense': [0.1, 0.2],
                'sparse': {'indices': [1], 'values': [0.8]},
            }
            for _ in chunks
        ]


class StubQueryEncoder:
    def encode(self, text):
        return type(
            'EncodedQuery',
            (),
            {
                'text': text,
                'dense': [0.1, 0.2],
                'sparse': {'indices': [1], 'values': [0.7]},
            },
        )()


class RecordingQdrantClient:
    def __init__(self):
        self.search_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        payload = {
            'document_key': 'doc1',
            'version_id': 'v1',
            'text': 'reset password policy',
            'metadata': {},
            'is_latest': True,
            'is_active': True,
        }
        return [{'id': 'chunk-1', 'score': 0.9, 'payload': payload}]


class StubCollectionManager:
    def __init__(self):
        self.calls = []

    def ensure_collection(self, definition):
        self.calls.append(definition)


def test_build_smoke_payload_produces_minimal_versioned_document_metadata():
    payload = build_smoke_payload(document_key='doc1', version_fingerprint='fp1')
    assert payload['document_key'] == 'doc1'
    assert payload['version_fingerprint'] == 'fp1'
    assert payload['source_system'] == 'smoke'



def test_run_live_smoke_builds_collection_payload_and_returns_dense_sparse_hit_summaries():
    collection_manager = StubCollectionManager()
    client = RecordingQdrantClient()

    result = run_live_smoke(
        document_key='doc1',
        version_fingerprint='fp1',
        chunks=['reset password policy'],
        query='reset password',
        document_encoder=StubDocumentEncoder(),
        query_encoder=StubQueryEncoder(),
        qdrant_client=client,
        collection_manager=collection_manager,
    )

    assert collection_manager.calls[0]['collection_name'] == 'documents'
    assert collection_manager.calls[0]['vectors_config']['dense']['size'] == 2
    assert collection_manager.calls[0]['sparse_vectors_config'] == {'sparse': {}}

    assert result['payload'] == {
        'document_key': 'doc1',
        'version_fingerprint': 'fp1',
        'source_system': 'smoke',
    }
    assert result['dense_hits'] == [{'chunk_id': 'chunk-1', 'document_key': 'doc1', 'score': 0.9}]
    assert result['sparse_hits'] == [{'chunk_id': 'chunk-1', 'document_key': 'doc1', 'score': 0.9}]

    assert client.search_calls[0]['query_vector'] == ('dense', [0.1, 0.2])
    assert client.search_calls[1]['query_vector'] == ('sparse', {'indices': [1], 'values': [0.7]})
