from rag_ingest.agno_specialist_agent import answer_query


class FakeBackend:
    def vector_search(self, query, limit):
        return [
            {
                'chunk_id': 'v1:0000',
                'text': 'Reset password in the portal.',
                'score': 0.9,
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
                'text': 'Reset password in the portal.',
                'score': 2.0,
                'document_key': 'doc1',
                'version_id': 'v1',
                'metadata': {},
                'is_latest': True,
                'is_active': True,
            }
        ]


def test_answer_query_returns_citation_aware_agent_answer():
    answer = answer_query('How do I reset password?', backend=FakeBackend())
    assert 'Reset password' in answer.answer
    assert answer.citations[0]['version_id'] == 'v1'
