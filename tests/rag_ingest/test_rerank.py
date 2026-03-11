import os

import pytest

from rag_ingest.http_reranker import HttpQwenReranker
from rag_ingest.rerank import rerank_candidates, select_reranker_from_env


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


def test_select_reranker_from_env_builds_http_qwen_adapter(monkeypatch):
    monkeypatch.setenv('RAG_RERANKER_PROVIDER', 'http_qwen')
    monkeypatch.setenv('RAG_RERANKER_BASE_URL', 'http://localhost:8090')
    monkeypatch.setenv('RAG_RERANKER_MODEL', 'Qwen3-Reranker-0.6B')

    reranker = select_reranker_from_env()

    assert isinstance(reranker, HttpQwenReranker)
    assert reranker.base_url == 'http://localhost:8090'
    assert reranker.model == 'Qwen3-Reranker-0.6B'


def test_select_reranker_from_env_returns_none_by_default(monkeypatch):
    for key in ['RAG_RERANKER_PROVIDER', 'RAG_RERANKER_BASE_URL', 'RAG_RERANKER_MODEL']:
        monkeypatch.delenv(key, raising=False)

    assert select_reranker_from_env() is None
