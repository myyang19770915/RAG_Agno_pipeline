import json
from urllib import request
from urllib.parse import urljoin


class HttpQwenReranker(object):
    name = 'http-qwen'

    def __init__(self, base_url, model, transport=None, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self._transport = transport or self._default_transport

    def rerank(self, query, candidates):
        documents = [candidate.get('text', '') for candidate in candidates]
        response = self._post_json(
            '/score',
            {
                'model': self.model,
                'query': query,
                'documents': documents,
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

        requested_are_unique = len(set(documents)) == len(documents)
        response_has_documents = all('document' in item for item in data)
        if requested_are_unique and response_has_documents:
            scores_by_document = {}
            for item in data:
                score = item.get('score')
                document = item.get('document')
                if score is None:
                    raise RuntimeError('reranker response item missing score field')
                if document not in documents:
                    raise RuntimeError('reranker response did not match requested documents')
                scores_by_document[document] = score
            if len(scores_by_document) != len(documents):
                raise RuntimeError('reranker response did not match requested documents')
            return [scores_by_document[document] for document in documents]

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
        }
        status, body = self._transport(http_request)
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
        with request.urlopen(raw_request) as response:
            return response.status, response.read()
