from rag_ingest.agent_answer_assembler import assemble_answer


def test_history_mode_adds_note_when_answer_uses_historical_context():
    response = {
        'results': [
            {
                'text': 'Old password reset process.',
                'document_key': 'doc1',
                'version_id': 'v0',
                'chunk_id': 'v0:0000',
                'citation': {'document_key': 'doc1', 'version_id': 'v0', 'chunk_id': 'v0:0000'},
            }
        ]
    }
    answer = assemble_answer('How did we reset passwords before?', response, history_mode=True)
    assert answer.notes
