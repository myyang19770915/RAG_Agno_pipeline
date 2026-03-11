import json
import pytest

from rag_ingest.http_embedding_adapter import HttpEmbeddingAdapter


class RecordingTransport:
    def __init__(self, response_payload=None, status=200):
        self.calls = []
        self.response_payload = response_payload or {
            'data': [
                {'embedding': [0.1, 0.2]},
                {'embedding': [0.3, 0.4]},
            ]
        }
        self.status = status

    def __call__(self, request):
        self.calls.append(request)
        return self.status, json.dumps(self.response_payload).encode('utf-8')


def test_http_embedding_adapter_posts_openai_compatible_payload():
    transport = RecordingTransport()
    adapter = HttpEmbeddingAdapter(
        base_url='http://localhost:8000/',
        model='Qwen/Qwen3-Embedding-0.6B',
        transport=transport,
    )

    result = adapter.embed_texts(['hello', 'world'])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    request = transport.calls[0]
    assert request['url'] == 'http://localhost:8000/v1/embeddings'
    assert request['headers']['Content-Type'] == 'application/json'
    assert request['body'] == {
        'model': 'Qwen/Qwen3-Embedding-0.6B',
        'input': ['hello', 'world'],
    }


def test_http_embedding_adapter_raises_for_missing_data_items():
    transport = RecordingTransport(response_payload={'data': [{}]})
    adapter = HttpEmbeddingAdapter(
        base_url='http://localhost:8000',
        model='embed-model',
        transport=transport,
    )

    with pytest.raises(RuntimeError, match='embedding'):
        adapter.embed_texts(['hello'])
