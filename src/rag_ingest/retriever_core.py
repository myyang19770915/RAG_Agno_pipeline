from typing import Any

from rag_ingest.citation_utils import format_retrieve_result
from rag_ingest.observability import build_event, timed_call
from rag_ingest.pre_retrieval import prepare_queries
from rag_ingest.rerank import rerank_candidates
from rag_ingest.retrieval_filters import filter_candidates
from rag_ingest.retrieval_fusion import fuse_ranked_results
from rag_ingest.retriever_schemas import RetrieveResponse


def retrieve(
    query: str,
    backend: Any,
    top_k: int = 5,
    rewrite_mode: str = 'none',
    history_mode: bool = False,
    filters: dict[str, Any] | None = None,
    include_debug: bool = False,
) -> RetrieveResponse:
    timings: dict[str, dict[str, float]] = {}

    prepared, prepare_timing = timed_call(
        'prepare_queries',
        lambda: prepare_queries(query, rewrite_mode=rewrite_mode),
    )
    timings['prepare_queries'] = {'elapsed_ms': prepare_timing['elapsed_ms']}

    def _collect_vector_candidates():
        vector_candidates: list[dict[str, Any]] = []
        for applied_query in prepared.applied_queries:
            vector_candidates.extend(backend.vector_search(applied_query, top_k))
        return vector_candidates

    vector_candidates, vector_timing = timed_call('vector_search', _collect_vector_candidates)
    timings['vector_search'] = {'elapsed_ms': vector_timing['elapsed_ms']}

    def _collect_keyword_candidates():
        keyword_candidates: list[dict[str, Any]] = []
        for applied_query in prepared.applied_queries:
            keyword_candidates.extend(backend.keyword_search(applied_query, top_k))
        return keyword_candidates

    keyword_candidates, keyword_timing = timed_call('keyword_search', _collect_keyword_candidates)
    timings['keyword_search'] = {'elapsed_ms': keyword_timing['elapsed_ms']}

    def _fuse_filter_and_rerank():
        fused_candidates = fuse_ranked_results(vector_candidates, keyword_candidates)
        filtered_candidates = filter_candidates(
            fused_candidates,
            history_mode=history_mode,
            extra_filters=filters,
        )
        if hasattr(backend, 'rerank'):
            reranked_candidates = backend.rerank(prepared.applied_query, filtered_candidates)
        else:
            reranked_candidates = rerank_candidates(
                prepared.applied_query,
                filtered_candidates,
                strategy='lightweight',
            )
        return fused_candidates, reranked_candidates

    (fused_candidates, reranked_candidates), total_timing = timed_call(
        'fusion_filter_rerank',
        _fuse_filter_and_rerank,
    )
    timings['fusion_filter_rerank'] = {'elapsed_ms': total_timing['elapsed_ms']}
    total_elapsed_ms = sum(stage['elapsed_ms'] for stage in timings.values())
    timings['total'] = {'elapsed_ms': total_elapsed_ms}

    results = [
        format_retrieve_result(
            text=candidate['text'],
            score=candidate.get('fused_score', candidate.get('score', 0.0)),
            document_key=candidate['document_key'],
            version_id=candidate['version_id'],
            chunk_id=candidate['chunk_id'],
            metadata=candidate.get('metadata'),
        )
        for candidate in reranked_candidates[:top_k]
    ]

    debug = None
    if include_debug:
        event = build_event(
            'retrieval.completed',
            operation='retrieve',
            status='ok',
            timing=timings['total'],
            summary={
                'vector_candidates': len(vector_candidates),
                'keyword_candidates': len(keyword_candidates),
                'fused_candidates': len(fused_candidates),
                'reranked_candidates': len(reranked_candidates),
                'results_returned': len(results),
            },
        )
        debug = {
            'rewrite_strategy': prepared.rewrite_strategy,
            'retrieval_summary': {
                'vector_candidates': len(vector_candidates),
                'keyword_candidates': len(keyword_candidates),
                'fused_candidates': len(fused_candidates),
                'reranked_candidates': len(reranked_candidates),
                'elapsed_ms': total_elapsed_ms,
            },
            'timings': timings,
            'event': event,
        }

    return RetrieveResponse(
        results=results,
        applied_query=prepared.applied_query,
        applied_queries=prepared.applied_queries,
        retrieval_mode='hybrid',
        debug=debug,
    )
