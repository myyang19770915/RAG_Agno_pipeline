from rag_ingest.agent_answer_assembler import assemble_answer


def test_assemble_answer_builds_summary_and_citations_from_retrieval_results():
    response = {
        'results': [
            {
                'text': 'Reset password in the user portal.',
                'document_key': 'doc1',
                'version_id': 'v1',
                'chunk_id': 'v1:0000',
                'citation': {'document_key': 'doc1', 'version_id': 'v1', 'chunk_id': 'v1:0000'},
            }
        ]
    }
    answer = assemble_answer('How do I reset password?', response)
    assert 'Reset password' in answer.answer
    assert answer.citations[0]['document_key'] == 'doc1'
