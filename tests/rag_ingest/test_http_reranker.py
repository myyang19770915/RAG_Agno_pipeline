import json
import pytest

from rag_ingest.http_reranker import HttpQwenReranker


class RecordingTransport:
    def __init__(self, response_payload=None, status=200):
        self.calls = []
        self.response_payload = response_payload or {
            'data': [
                {'score': 0.1},
                {'score': 0.9},
            ]
        }
        self.status = status

    def __call__(self, request):
        self.calls.append(request)
        return self.status, json.dumps(self.response_payload).encode('utf-8')


def test_http_qwen_reranker_posts_queries_items_payload_and_sorts_candidates():
    transport = RecordingTransport()
    reranker = HttpQwenReranker(
        base_url='http://localhost:8090/',
        model='Qwen3-Reranker-0.6B',
        transport=transport,
    )
    candidates = [
        {'chunk_id': 'a', 'text': 'first', 'score': 0.2},
        {'chunk_id': 'b', 'text': 'second', 'score': 0.1},
    ]

    reranked = reranker.rerank('which document wins', candidates)

    assert [item['chunk_id'] for item in reranked] == ['b', 'a']
    request = transport.calls[0]
    assert request['url'] == 'http://localhost:8090/score'
    assert request['body'] == {
        'model': 'Qwen3-Reranker-0.6B',
        'queries': ['which document wins'],
        'items': ['first', 'second'],
    }


def test_http_qwen_reranker_preserves_response_index_order_for_scores():
    transport = RecordingTransport(
        response_payload={
            'data': [
                {'score': 0.8},
                {'score': 0.2},
            ]
        }
    )
    reranker = HttpQwenReranker(
        base_url='http://localhost:8090',
        model='rerank-model',
        transport=transport,
    )

    reranked = reranker.rerank(
        'query',
        [
            {'chunk_id': 'a', 'text': 'first'},
            {'chunk_id': 'b', 'text': 'second'},
        ],
    )

    assert [item['chunk_id'] for item in reranked] == ['a', 'b']
    assert [item['rerank_score'] for item in reranked] == [0.8, 0.2]


def test_http_qwen_reranker_uses_data_index_order_even_when_documents_are_present():
    transport = RecordingTransport(
        response_payload={
            'data': [
                {'document': 'second', 'score': 0.8},
                {'document': 'first', 'score': 0.2},
            ]
        }
    )
    reranker = HttpQwenReranker(
        base_url='http://localhost:8090',
        model='rerank-model',
        transport=transport,
    )

    reranked = reranker.rerank(
        'query',
        [
            {'chunk_id': 'a', 'text': 'first'},
            {'chunk_id': 'b', 'text': 'second'},
        ],
    )

    assert [item['chunk_id'] for item in reranked] == ['a', 'b']
    assert [item['rerank_score'] for item in reranked] == [0.8, 0.2]


def test_http_qwen_reranker_supports_duplicate_document_texts():
    transport = RecordingTransport(
        response_payload={
            'data': [
                {'score': 0.2},
                {'score': 0.8},
            ]
        }
    )
    reranker = HttpQwenReranker(
        base_url='http://localhost:8090',
        model='rerank-model',
        transport=transport,
    )

    reranked = reranker.rerank(
        'query',
        [
            {'chunk_id': 'a', 'text': 'duplicate'},
            {'chunk_id': 'b', 'text': 'duplicate'},
        ],
    )

    assert [item['chunk_id'] for item in reranked] == ['b', 'a']
    assert [item['rerank_score'] for item in reranked] == [0.8, 0.2]


def test_http_qwen_reranker_raises_when_scores_do_not_match_documents():
    transport = RecordingTransport(response_payload={'data': [{'score': 0.5}]})
    reranker = HttpQwenReranker(
        base_url='http://localhost:8090',
        model='rerank-model',
        transport=transport,
    )

    with pytest.raises(RuntimeError, match='documents'):
        reranker.rerank(
            'query',
            [
                {'chunk_id': 'a', 'text': 'first'},
                {'chunk_id': 'b', 'text': 'second'},
            ],
        )
