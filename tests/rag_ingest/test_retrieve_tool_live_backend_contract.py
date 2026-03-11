from rag_ingest.qdrant_retriever_backend import QdrantRetrieverBackend
from rag_ingest.query_encoders import StaticQueryEncoder
from rag_ingest.retriever_tool import retrieve_tool


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


def test_retrieve_tool_still_returns_plain_dict_with_live_backend_adapter_shape():
    backend = QdrantRetrieverBackend(
        client=FakeClient(),
        query_encoder=StaticQueryEncoder([0.1, 0.2], {'indices': [1], 'values': [0.7]}),
    )

    response = retrieve_tool({'query': 'reset password', 'top_k': 1}, backend=backend)

    assert response['results'][0]['chunk_id'] == 'v1:0000'
    assert response['results'][0]['citation']['version_id'] == 'v1'
