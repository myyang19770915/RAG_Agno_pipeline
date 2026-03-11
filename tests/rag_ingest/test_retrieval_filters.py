from rag_ingest.retrieval_filters import filter_candidates


def test_default_filter_keeps_latest_active_only():
    candidates = [
        {'chunk_id': 'a', 'is_latest': True, 'is_active': True},
        {'chunk_id': 'b', 'is_latest': False, 'is_active': True},
        {'chunk_id': 'c', 'is_latest': True, 'is_active': False},
    ]

    filtered = filter_candidates(candidates, history_mode=False)

    assert [item['chunk_id'] for item in filtered] == ['a']



def test_history_mode_allows_non_latest_versions():
    candidates = [
        {'chunk_id': 'a', 'is_latest': True, 'is_active': True},
        {'chunk_id': 'b', 'is_latest': False, 'is_active': True},
    ]

    filtered = filter_candidates(candidates, history_mode=True)

    assert {item['chunk_id'] for item in filtered} == {'a', 'b'}
