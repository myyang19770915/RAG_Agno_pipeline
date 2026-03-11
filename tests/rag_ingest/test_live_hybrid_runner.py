from rag_ingest.live_hybrid_runner import (
    build_live_summary,
    run_live_hybrid,
)


class FakeRuntime:
    def encode_chunks(self, chunks):
        return [
            {
                'dense': [0.1, 0.2],
                'sparse': {'indices': [index + 1], 'values': [1.0]},
            }
            for index, _chunk in enumerate(chunks)
        ]

    def encode_query(self, text):
        return {
            'dense': [0.5, 0.6],
            'sparse': {'indices': [9], 'values': [0.9]},
        }


class FakeQdrantOps:
    def __init__(self):
        self.ensure_calls = []
        self.upserted_points = None
        self.dense_queries = []
        self.sparse_queries = []

    def ensure_collection(self, collection):
        self.ensure_calls.append(collection)

    def upsert_points(self, points):
        self.upserted_points = points

    def query_dense(self, vector, limit=5):
        self.dense_queries.append((vector, limit))
        return [{'id': 'dense-hit', 'score': 0.91, 'payload': {'chunk_id': 'ver-1:0000', 'document_key': 'doc-key'}}]

    def query_sparse(self, vector, limit=5):
        self.sparse_queries.append((vector, limit))
        return [{'id': 'sparse-hit', 'score': 0.73, 'payload': {'chunk_id': 'ver-1:0001', 'document_key': 'doc-key'}}]


def test_run_live_hybrid_encodes_upserts_and_queries_with_safe_ids():
    summary = run_live_hybrid(
        chunks=['alpha', 'beta'],
        query='find alpha',
        version_id='ver-1',
        document_id='doc-1',
        document_key='doc-key',
        runtime=FakeRuntime(),
        qdrant_ops=FakeQdrantOps(),
        collection_name='hybrid_live_test',
    )

    assert summary['collection']['collection_name'] == 'hybrid_live_test'
    assert summary['point_count'] == 2
    assert summary['points'][0]['id'] != summary['points'][0]['chunk_id']
    assert summary['points'][0]['chunk_id'] == 'ver-1:0000'
    assert summary['dense_hits'][0]['chunk_id'] == 'ver-1:0000'
    assert summary['sparse_hits'][0]['chunk_id'] == 'ver-1:0001'


def test_build_live_summary_returns_compact_shape():
    summary = build_live_summary(
        collection={'collection_name': 'hybrid_live_test'},
        points=[
            {'id': 'p1', 'payload': {'chunk_id': 'ver-1:0000', 'document_key': 'doc-key'}},
            {'id': 'p2', 'payload': {'chunk_id': 'ver-1:0001', 'document_key': 'doc-key'}},
        ],
        dense_hits=[{'chunk_id': 'ver-1:0000', 'score': 0.91, 'document_key': 'doc-key'}],
        sparse_hits=[{'chunk_id': 'ver-1:0001', 'score': 0.73, 'document_key': 'doc-key'}],
    )

    assert summary == {
        'collection': {'collection_name': 'hybrid_live_test'},
        'point_count': 2,
        'points': [
            {'id': 'p1', 'chunk_id': 'ver-1:0000', 'document_key': 'doc-key'},
            {'id': 'p2', 'chunk_id': 'ver-1:0001', 'document_key': 'doc-key'},
        ],
        'dense_hits': [{'chunk_id': 'ver-1:0000', 'score': 0.91, 'document_key': 'doc-key'}],
        'sparse_hits': [{'chunk_id': 'ver-1:0001', 'score': 0.73, 'document_key': 'doc-key'}],
    }
