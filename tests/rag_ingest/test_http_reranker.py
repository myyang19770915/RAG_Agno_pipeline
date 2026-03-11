import json
import pytest

from rag_ingest.http_reranker import HttpQwenReranker


class RecordingTransport:
    def __init__(self, response_payload=None, status=200):
        self.calls = []
        self.response_payload = response_payload or {
            'data': [
                {'document': 'second', 'score': 0.9},
                {'document': 'first', 'score': 0.1},
            ]
        }
        self.status = status

    def __call__(self, request):
        self.calls.append(request)
        return self.status, json.dumps(self.response_payload).encode('utf-8')


def test_http_qwen_reranker_posts_score_payload_and_sorts_candidates():
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
        'query': 'which document wins',
        'documents': ['first', 'second'],
    }


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
