from rag_ingest.pre_retrieval import prepare_queries


def test_none_mode_returns_original_query_only():
    prepared = prepare_queries('reset password', rewrite_mode='none')
    assert prepared.applied_query == 'reset password'
    assert prepared.applied_queries == ['reset password']


def test_rewrite_only_normalizes_whitespace_and_case():
    prepared = prepare_queries('  Reset   Password  ', rewrite_mode='rewrite_only')
    assert prepared.applied_query == 'reset password'
    assert prepared.applied_queries == ['reset password']


def test_multi_query_adds_expanded_queries_without_losing_original_meaning():
    prepared = prepare_queries('vpn login issue', rewrite_mode='multi_query')
    assert 'vpn login issue' in prepared.applied_queries
    assert len(prepared.applied_queries) >= 2
