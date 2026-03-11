from rag_ingest.retriever_core import retrieve


class FakeHybridBackend:
    def vector_search(self, query, limit):
        return [
            {
                'chunk_id': 'v1:0000',
                'text': 'reset password policy',
                'score': 0.7,
                'document_key': 'doc1',
                'version_id': 'v1',
                'metadata': {},
                'is_latest': True,
                'is_active': True,
            }
        ]

    def keyword_search(self, query, limit):
        return [
            {
                'chunk_id': 'v1:0000',
                'text': 'reset password policy',
                'score': 7.0,
                'document_key': 'doc1',
                'version_id': 'v1',
                'metadata': {},
                'is_latest': True,
                'is_active': True,
            }
        ]


def test_retrieve_keeps_same_external_contract_with_realistic_hybrid_backend_shape():
    response = retrieve('reset password', backend=FakeHybridBackend(), top_k=1)
    assert response.results[0].chunk_id == 'v1:0000'
    assert response.results[0].citation['document_key'] == 'doc1'
