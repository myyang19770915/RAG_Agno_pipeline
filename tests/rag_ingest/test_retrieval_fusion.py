from rag_ingest.retrieval_fusion import fuse_ranked_results


def test_rrf_fusion_promotes_items_seen_in_both_lists():
    vector_results = [
        {'chunk_id': 'a', 'score': 0.9},
        {'chunk_id': 'b', 'score': 0.8},
    ]
    keyword_results = [
        {'chunk_id': 'b', 'score': 10.0},
        {'chunk_id': 'c', 'score': 9.0},
    ]
    fused = fuse_ranked_results(vector_results, keyword_results)
    assert fused[0]['chunk_id'] == 'b'


def test_fusion_deduplicates_by_chunk_id():
    fused = fuse_ranked_results(
        [{'chunk_id': 'x', 'score': 0.4}],
        [{'chunk_id': 'x', 'score': 3.0}],
    )
    assert len(fused) == 1
