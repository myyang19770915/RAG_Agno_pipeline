from rag_ingest.agent_answers import AgentAnswer


def test_agent_answer_keeps_answer_and_citations():
    answer = AgentAnswer(
        answer='Reset your password in the portal.',
        citations=[{'document_key': 'doc1', 'version_id': 'v1', 'chunk_id': 'v1:0000'}],
        used_chunks_count=1,
    )
    assert answer.used_chunks_count == 1
    assert answer.citations[0]['chunk_id'] == 'v1:0000'
