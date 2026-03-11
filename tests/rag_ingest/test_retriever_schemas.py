from rag_ingest.retriever_schemas import RetrieveRequest, RetrieveResult, RetrieveResponse


def test_retrieve_request_defaults_are_agent_friendly():
    req = RetrieveRequest(query='how to reset password')
    assert req.top_k == 5
    assert req.rewrite_mode == 'none'
    assert req.history_mode is False
    assert req.include_debug is False


def test_retrieve_result_keeps_full_traceable_citation_fields():
    result = RetrieveResult(
        text='Reset your password from Settings.',
        score=0.91,
        document_key='sharepoint:SOP-001',
        version_id='ver_3',
        chunk_id='ver_3:0007',
        metadata={'source_system': 'sharepoint'},
        citation={
            'document_key': 'sharepoint:SOP-001',
            'version_id': 'ver_3',
            'chunk_id': 'ver_3:0007',
        },
    )
    assert result.citation['version_id'] == 'ver_3'


def test_retrieve_response_can_hold_multiple_applied_queries():
    response = RetrieveResponse(
        results=[],
        applied_query='reset password',
        applied_queries=['reset password', 'password reset policy'],
        retrieval_mode='hybrid',
    )
    assert len(response.applied_queries) == 2
