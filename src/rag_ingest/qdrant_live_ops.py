from qdrant_client import models

from rag_ingest.qdrant_integration import payload_index_fields, latest_active_query_filter, version_points_selector


class LiveQdrantOps(object):
    def __init__(self, client, collection_name='documents'):
        self.client = client
        self.collection_name = collection_name

    def ensure_collection(self, vector_size, distance=models.Distance.COSINE):
        names = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=distance),
            )
        for field in payload_index_fields():
            schema = models.PayloadSchemaType.KEYWORD
            if field in ('is_latest', 'is_active'):
                schema = models.PayloadSchemaType.BOOL
            self.client.create_payload_index(self.collection_name, field, schema)

    def upsert_points(self, points):
        self.client.upsert(collection_name=self.collection_name, points=points)

    def mark_old_version_inactive(self, version_id):
        self.client.set_payload(
            collection_name=self.collection_name,
            payload={'is_latest': False, 'is_active': False},
            points=models.FilterSelector(filter=models.Filter(must=[models.FieldCondition(key='version_id', match=models.MatchValue(value=version_id))])),
        )

    def delete_inactive_version(self, version_id):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=models.Filter(must=[models.FieldCondition(key='version_id', match=models.MatchValue(value=version_id)), models.FieldCondition(key='is_active', match=models.MatchValue(value=False))])),
        )

    def latest_filter(self):
        f = latest_active_query_filter()
        return models.Filter(must=[models.FieldCondition(key=i['key'], match=models.MatchValue(value=i['match']['value'])) for i in f['must']])

    def query_latest(self, vector, limit=5):
        return self.client.query_points(collection_name=self.collection_name, query=vector, limit=limit, with_payload=True, query_filter=self.latest_filter())

    def version_selector(self, version_id):
        f = version_points_selector(version_id)
        return models.Filter(must=[models.FieldCondition(key=i['key'], match=models.MatchValue(value=i['match']['value'])) for i in f['must']])
