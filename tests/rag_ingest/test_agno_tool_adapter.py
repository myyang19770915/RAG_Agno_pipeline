from rag_ingest.agno_tool_adapter import retrieve_knowledge


class FakeBackend:
    def vector_search(self, query, limit):
        return []

    def keyword_search(self, query, limit):
        return []


def test_retrieve_knowledge_delegates_to_retrieve_tool():
    response = retrieve_knowledge(
        query='reset password',
        backend=FakeBackend(),
        top_k=3,
    )
    assert response['retrieval_mode'] == 'hybrid'
