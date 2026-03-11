from rag_ingest.qdrant_filters import latest_active_filter
from rag_ingest.rerank import rerank_candidates


def build_dense_query_args(vector, limit, query_filter=None):
    return {
        'query_vector': ('dense', vector),
        'query_filter': latest_active_filter() if query_filter is None else query_filter,
        'limit': limit,
    }


def build_sparse_query_args(vector, limit, query_filter=None):
    return {
        'query_vector': ('sparse', vector),
        'query_filter': latest_active_filter() if query_filter is None else query_filter,
        'limit': limit,
    }


def _hit_value(hit, key, default=None):
    if isinstance(hit, dict):
        return hit.get(key, default)
    return getattr(hit, key, default)


def normalize_qdrant_result(hit):
    payload = _hit_value(hit, 'payload', {}) or {}
    return {
        'chunk_id': _hit_value(hit, 'id'),
        'text': payload.get('text', ''),
        'score': _hit_value(hit, 'score', 0.0),
        'document_key': payload.get('document_key'),
        'version_id': payload.get('version_id'),
        'metadata': payload.get('metadata', {}),
        'is_latest': payload.get('is_latest', False),
        'is_active': payload.get('is_active', False),
    }


class QdrantRetrieverBackend(object):
    def __init__(self, client, collection_name='documents', query_encoder=None, reranker=None):
        self.client = client
        self.collection_name = collection_name
        self.query_encoder = query_encoder
        self.reranker = reranker

    def _encode_query(self, query):
        if self.query_encoder is None:
            return None
        return self.query_encoder.encode(query)

    def _search_points(self, *, query_vector, query_filter, limit):
        if hasattr(self.client, 'search'):
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
            )
            return hits

        if hasattr(self.client, 'query_points'):
            using, vector = query_vector
            if using == 'sparse':
                from qdrant_client.http import models

                vector = models.SparseVector(
                    indices=vector.get('indices', []),
                    values=vector.get('values', []),
                )
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                using=using,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            return getattr(response, 'points', response)

        raise RuntimeError('Qdrant client does not support search/query_points APIs')

    def vector_search(self, query, limit):
        encoded = self._encode_query(query)
        if encoded is None:
            return []

        hits = self._search_points(**build_dense_query_args(encoded.dense, limit))
        return [normalize_qdrant_result(hit) for hit in hits]

    def keyword_search(self, query, limit):
        encoded = self._encode_query(query)
        if encoded is None:
            return []

        hits = self._search_points(**build_sparse_query_args(encoded.sparse, limit))
        return [normalize_qdrant_result(hit) for hit in hits]

    def rerank(self, query, candidates):
        if self.reranker is None:
            return rerank_candidates(query, candidates, strategy='lightweight')
        return self.reranker.rerank(query, candidates)

    def hybrid_search(self, query, limit):
        vector_results = self.vector_search(query, limit)
        keyword_results = self.keyword_search(query, limit)
        return {
            'vector': vector_results,
            'keyword': keyword_results,
        }
