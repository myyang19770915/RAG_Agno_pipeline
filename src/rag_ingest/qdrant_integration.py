def collection_definition(vector_size, collection_name='documents', distance='cosine'):
    return {
        'collection_name': collection_name,
        'vector_size': vector_size,
        'distance': distance,
        'vectors_config': {
            'dense': {
                'size': vector_size,
                'distance': distance,
            }
        },
        'sparse_vectors_config': {
            'sparse': {}
        },
        'on_disk_payload': True,
    }


def payload_index_fields():
    return [
        'document_key',
        'version_id',
        'business_id',
        'source_system',
        'is_latest',
        'is_active',
        'doc_type',
    ]


def latest_active_query_filter():
    return {
        'must': [
            {'key': 'is_latest', 'match': {'value': True}},
            {'key': 'is_active', 'match': {'value': True}},
        ]
    }


def version_points_selector(version_id):
    return {
        'must': [
            {'key': 'version_id', 'match': {'value': version_id}},
        ]
    }


class QdrantClientFactory(object):
    def __init__(self, url='http://localhost:6333', api_key=None):
        self.url = url
        self.api_key = api_key

    def create(self):
        try:
            from qdrant_client import QdrantClient
        except Exception:
            raise RuntimeError('qdrant_client not installed')
        return QdrantClient(url=self.url, api_key=self.api_key)
