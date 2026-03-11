from rag_ingest.retriever_tool import retrieve_tool


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
            }
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
            }
        ]


def test_retrieve_tool_accepts_structured_request_dict():
    response = retrieve_tool(
        {
            'query': 'reset password',
            'top_k': 1,
            'rewrite_mode': 'none',
            'history_mode': False,
        },
        backend=FakeBackend(),
    )
    assert response['retrieval_mode'] == 'hybrid'
    assert response['results'][0]['chunk_id'] == 'a'
