import json
from urllib import request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin


class HttpQwenReranker(object):
    name = 'http-qwen'

    def __init__(self, base_url, model, transport=None, api_key=None, timeout_seconds=10):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self._transport = transport or self._default_transport

    def rerank(self, query, candidates):
        documents = [candidate.get('text', '') for candidate in candidates]
        response = self._post_json(
            '/score',
            {
                'model': self.model,
                'queries': [query],
                'items': documents,
            },
        )
        scores = self._extract_scores(response, documents)
        reranked = []
        for index, candidate in enumerate(candidates):
            updated = dict(candidate)
            updated['rerank_score'] = scores[index]
            reranked.append(updated)
        return sorted(reranked, key=lambda item: item['rerank_score'], reverse=True)

    def _extract_scores(self, response, documents):
        data = response.get('data')
        if not isinstance(data, list) or len(data) != len(documents):
            raise RuntimeError('reranker response did not match requested documents')

        scores = []
        for item in data:
            score = item.get('score')
            if score is None:
                raise RuntimeError('reranker response item missing score field')
            scores.append(score)
        return scores

    def _post_json(self, path, payload):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = 'Bearer %s' % self.api_key
        http_request = {
            'url': urljoin(self.base_url + '/', path.lstrip('/')),
            'headers': headers,
            'body': payload,
            'timeout': self.timeout_seconds,
        }
        try:
            status, body = self._transport(http_request)
        except HTTPError as exc:
            raise RuntimeError('reranker request failed with status %s' % exc.code)
        except URLError as exc:
            raise RuntimeError('reranker request failed: %s' % exc.reason)
        except Exception as exc:
            raise RuntimeError('reranker request failed: %s' % exc)
        if status >= 400:
            raise RuntimeError('reranker request failed with status %s' % status)
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
