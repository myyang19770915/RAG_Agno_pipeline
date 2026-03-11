import json
from urllib import request
from urllib.parse import urljoin


class HttpEmbeddingAdapter(object):
    name = 'http-openai-compatible'

    def __init__(self, base_url, model, transport=None, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self._transport = transport or self._default_transport

    def embed_texts(self, texts):
        response = self._post_json(
            'v1/embeddings',
            {
                'model': self.model,
                'input': list(texts),
            },
        )
        data = response.get('data') or []
        vectors = []
        for item in data:
            embedding = item.get('embedding')
            if embedding is None:
                raise RuntimeError('embedding response item missing embedding field')
            vectors.append(embedding)
        return vectors

    def _post_json(self, path, payload):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = 'Bearer %s' % self.api_key
        http_request = {
            'url': urljoin(self.base_url + '/', path),
            'headers': headers,
            'body': payload,
        }
        status, body = self._transport(http_request)
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
        with request.urlopen(raw_request) as response:
            return response.status, response.read()
