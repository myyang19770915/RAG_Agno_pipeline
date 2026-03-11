from rag_ingest.qdrant_integration import payload_index_fields, collection_definition, latest_active_query_filter, version_points_selector


class QdrantRuntimeAdapter(object):
    def __init__(self, client, collection_name='documents'):
        self.client = client
        self.collection_name = collection_name

    def ensure_collection(self, vector_size):
        cfg = collection_definition(vector_size=vector_size, collection_name=self.collection_name)
        return cfg

    def ensure_payload_indexes(self):
        return payload_index_fields()

    def latest_filter(self):
        return latest_active_query_filter()

    def version_selector(self, version_id):
        return version_points_selector(version_id)
