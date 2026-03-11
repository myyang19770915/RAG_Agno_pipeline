from rag_ingest.agent_answers import AgentAnswer
from rag_ingest.agent_response_formatter import format_agent_response


def test_format_agent_response_outputs_answer_and_human_readable_citations():
    answer = AgentAnswer(
        answer='Reset your password in the portal.',
        citations=[{'document_key': 'doc1', 'version_id': 'v1', 'chunk_id': 'v1:0000'}],
        used_chunks_count=1,
    )
    text = format_agent_response(answer)
    assert 'Reset your password' in text
    assert 'doc1' in text
