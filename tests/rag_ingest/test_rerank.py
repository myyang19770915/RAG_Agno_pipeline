from rag_ingest.rerank import rerank_candidates


def test_lightweight_rerank_prefers_stronger_query_overlap():
    query = 'reset password policy'
    candidates = [
        {'chunk_id': 'a', 'text': 'reset password policy steps', 'score': 0.4},
        {'chunk_id': 'b', 'text': 'vpn access troubleshooting', 'score': 0.9},
    ]

    reranked = rerank_candidates(query, candidates, strategy='lightweight')

    assert reranked[0]['chunk_id'] == 'a'


def test_none_strategy_returns_original_order():
    candidates = [
        {'chunk_id': 'a', 'text': 'alpha', 'score': 0.3},
        {'chunk_id': 'b', 'text': 'beta', 'score': 0.2},
    ]

    reranked = rerank_candidates('anything', candidates, strategy='none')

    assert [item['chunk_id'] for item in reranked] == ['a', 'b']
