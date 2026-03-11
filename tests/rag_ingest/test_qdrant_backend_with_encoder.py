from rag_ingest.qdrant_retriever_backend import QdrantRetrieverBackend


class RecordingEncoder:
    def __init__(self):
        self.calls = []

    def encode(self, text):
        self.calls.append(text)
        return type(
            'EncodedQuery',
            (),
            {
                'text': text,
                'dense': [0.1, 0.2],
                'sparse': {'indices': [1], 'values': [0.7]},
            },
        )()


class FakeClient:
    def search(self, **kwargs):
        return [
            {
                'id': 'v1:0000',
                'score': 0.9,
                'payload': {
                    'text': 'reset password policy',
                    'document_key': 'doc1',
                    'version_id': 'v1',
                    'is_latest': True,
                    'is_active': True,
                },
            }
        ]


def test_backend_uses_unified_encoder_for_dense_and_sparse_queries():
    encoder = RecordingEncoder()
    backend = QdrantRetrieverBackend(
        client=FakeClient(),
        query_encoder=encoder,
    )

    assert backend.vector_search('reset password', 1)[0]['chunk_id'] == 'v1:0000'
    assert backend.keyword_search('reset password', 1)[0]['chunk_id'] == 'v1:0000'
    assert encoder.calls == ['reset password', 'reset password']
