from rag_ingest.qdrant_retriever_backend import QdrantRetrieverBackend
from rag_ingest.query_encoders import StaticQueryEncoder


class FakeQueryResponse:
    def __init__(self, points):
        self.points = points


class FakePoint:
    def __init__(self, point_id, score, payload):
        self.id = point_id
        self.score = score
        self.payload = payload


class QueryPointsOnlyClient:
    def __init__(self):
        self.calls = []

    def query_points(self, **kwargs):
        self.calls.append(kwargs)
        return FakeQueryResponse(
            [
                FakePoint(
                    'v1:0000',
                    0.91,
                    {
                        'text': 'reset password policy steps',
                        'document_key': 'doc1',
                        'version_id': 'v1',
                        'is_latest': True,
                        'is_active': True,
                    },
                )
            ]
        )


def test_backend_uses_query_points_when_search_api_is_unavailable():
    backend = QdrantRetrieverBackend(
        client=QueryPointsOnlyClient(),
        collection_name='documents',
        query_encoder=StaticQueryEncoder(
            dense_vector=[0.1, 0.2],
            sparse_vector={'indices': [1, 3], 'values': [0.4, 0.6]},
        ),
    )

    vector_hits = backend.vector_search('reset password', 3)
    keyword_hits = backend.keyword_search('reset password', 3)

    assert vector_hits[0]['chunk_id'] == 'v1:0000'
    assert keyword_hits[0]['document_key'] == 'doc1'
    assert len(backend.client.calls) == 2
    assert backend.client.calls[0]['using'] == 'dense'
    assert backend.client.calls[1]['using'] == 'sparse'
