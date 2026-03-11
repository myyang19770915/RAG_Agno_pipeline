from rag_ingest.retriever_core import retrieve


class FakeBackend:
    def vector_search(self, query, limit):
        return [
            {
                'chunk_id': 'a',
                'text': 'reset password policy steps',
                'score': 0.7,
                'document_key': 'doc1',
                'version_id': 'v1',
                'metadata': {},
                'is_latest': True,
                'is_active': True,
            },
            {
                'chunk_id': 'b',
                'text': 'old reset guide',
                'score': 0.9,
                'document_key': 'doc1',
                'version_id': 'v0',
                'metadata': {},
                'is_latest': False,
                'is_active': True,
            },
        ]

    def keyword_search(self, query, limit):
        return [
            {
                'chunk_id': 'a',
                'text': 'reset password policy steps',
                'score': 5.0,
                'document_key': 'doc1',
                'version_id': 'v1',
                'metadata': {},
                'is_latest': True,
                'is_active': True,
            },
        ]


def test_retrieve_runs_full_pipeline_and_returns_traceable_results():
    response = retrieve('reset password', backend=FakeBackend(), top_k=3, rewrite_mode='rewrite_only')
    assert response.retrieval_mode == 'hybrid'
    assert response.results[0].chunk_id == 'a'
    assert response.results[0].citation['version_id'] == 'v1'
    assert all(item.version_id != 'v0' for item in response.results)
