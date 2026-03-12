import json
from urllib import request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin


class HttpEmbeddingAdapter(object):
    name = 'http-openai-compatible'

    def __init__(self, base_url, model, transport=None, api_key=None, timeout_seconds=10):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self._transport = transport or self._default_transport

    def embed_texts(self, texts):
        inputs = list(texts)
        response = self._post_json(
            'v1/embeddings',
            {
                'model': self.model,
                'input': inputs,
            },
        )
        data = response.get('data') or []
        if len(data) != len(inputs):
            raise RuntimeError('embedding response did not match requested inputs')

        indexed_vectors = [None] * len(inputs)
        for position, item in enumerate(data):
            embedding = item.get('embedding')
            if embedding is None:
                raise RuntimeError('embedding response item missing embedding field')
            index = item.get('index', position)
            if not isinstance(index, int) or index < 0 or index >= len(inputs):
                raise RuntimeError('embedding response item had invalid index')
            indexed_vectors[index] = embedding

        if any(vector is None for vector in indexed_vectors):
            raise RuntimeError('embedding response did not match requested inputs')
        return indexed_vectors

    def _post_json(self, path, payload):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = 'Bearer %s' % self.api_key
        http_request = {
            'url': urljoin(self.base_url + '/', path),
            'headers': headers,
            'body': payload,
            'timeout': self.timeout_seconds,
        }
        try:
            status, body = self._transport(http_request)
        except HTTPError as exc:
            raise RuntimeError('embedding request failed with status %s' % exc.code)
        except URLError as exc:
            raise RuntimeError('embedding request failed: %s' % exc.reason)
        except Exception as exc:
            raise RuntimeError('embedding request failed: %s' % exc)
        if status >= 400:
            raise RuntimeError('embedding request failed with status %s' % status)
        return json.loads(body.decode('utf-8'))

    def _default_transport(self, http_request):
        raw_request = request.Request(
            http_request['url'],
            data=json.dumps(http_request['body']).encode('utf-8'),
            headers=http_request['headers'],
            method='POST',
        )
        with request.urlopen(raw_request, timeout=http_request['timeout']) as response:
            return response.status, response.read()
