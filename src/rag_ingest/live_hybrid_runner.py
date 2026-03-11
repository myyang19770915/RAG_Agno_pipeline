import argparse
import json
from uuid import uuid4

from rag_ingest.fastembed_adapters import FastEmbedAdapterConfig, FastEmbedRuntimeFactory
from rag_ingest.qdrant_hybrid_live_ops import build_hybrid_point_struct
from rag_ingest.qdrant_integration import QdrantClientFactory, collection_definition
from rag_ingest.qdrant_payloads import build_payload


class LiveHybridQdrantOps:
    def __init__(self, client, collection_name='documents'):
        self.client = client
        self.collection_name = collection_name

    def ensure_collection(self, collection):
        try:
            from qdrant_client import models
        except Exception as exc:
            raise RuntimeError('qdrant_client not installed') from exc

        names = [item.name for item in self.client.get_collections().collections]
        if self.collection_name not in names:
            dense_cfg = collection['vectors_config']['dense']
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    'dense': models.VectorParams(
                        size=dense_cfg['size'],
                        distance=models.Distance.COSINE,
                    )
                },
                sparse_vectors_config={'sparse': models.SparseVectorParams()},
                on_disk_payload=collection.get('on_disk_payload', True),
            )

        for field in ['document_key', 'version_id', 'is_latest', 'is_active', 'chunk_id']:
            schema = models.PayloadSchemaType.KEYWORD
            if field in ('is_latest', 'is_active'):
                schema = models.PayloadSchemaType.BOOL
            self.client.create_payload_index(self.collection_name, field, schema)

    def upsert_points(self, points):
        try:
            from qdrant_client import models
        except Exception as exc:
            raise RuntimeError('qdrant_client not installed') from exc
        structs = [
            models.PointStruct(
                id=point['id'],
                vector=point['vector'],
                payload=point['payload'],
            )
            for point in points
        ]
        self.client.upsert(collection_name=self.collection_name, points=structs)

    def query_dense(self, vector, limit=5):
        try:
            from qdrant_client import models
        except Exception as exc:
            raise RuntimeError('qdrant_client not installed') from exc
        result = self.client.http.search_api.search_points(
            collection_name=self.collection_name,
            search_request=models.SearchRequest(
                vector=models.NamedVector(name='dense', vector=vector),
                filter=self._latest_filter(models),
                limit=limit,
                with_payload=True,
            ),
        )
        return [self._point_to_dict(point) for point in result.result]

    def query_sparse(self, vector, limit=5):
        try:
            from qdrant_client import models
        except Exception as exc:
            raise RuntimeError('qdrant_client not installed') from exc
        result = self.client.http.search_api.search_points(
            collection_name=self.collection_name,
            search_request=models.SearchRequest(
                vector=models.NamedSparseVector(
                    name='sparse',
                    vector=models.SparseVector(indices=vector['indices'], values=vector['values']),
                ),
                filter=self._latest_filter(models),
                limit=limit,
                with_payload=True,
            ),
        )
        return [self._point_to_dict(point) for point in result.result]

    @staticmethod
    def _latest_filter(models):
        return models.Filter(
            must=[
                models.FieldCondition(key='is_latest', match=models.MatchValue(value=True)),
                models.FieldCondition(key='is_active', match=models.MatchValue(value=True)),
            ]
        )

    @staticmethod
    def _point_to_dict(point):
        return {
            'id': str(point.id),
            'score': point.score,
            'payload': point.payload or {},
        }


def _compact_hit(hit):
    payload = hit.get('payload', {})
    return {
        'chunk_id': payload.get('chunk_id', hit.get('chunk_id')),
        'score': hit.get('score'),
        'document_key': payload.get('document_key', hit.get('document_key')),
    }


def build_live_summary(*, collection, points, dense_hits, sparse_hits):
    return {
        'collection': collection,
        'point_count': len(points),
        'points': [
            {
                'id': point['id'],
                'chunk_id': point['payload'].get('chunk_id'),
                'document_key': point['payload'].get('document_key'),
            }
            for point in points
        ],
        'dense_hits': [_compact_hit(hit) for hit in dense_hits],
        'sparse_hits': [_compact_hit(hit) for hit in sparse_hits],
    }


def run_live_hybrid(
    *,
    chunks,
    query,
    version_id,
    document_id,
    document_key,
    runtime,
    qdrant_ops,
    collection_name='documents',
    version_no=1,
):
    encoded_chunks = runtime.encode_chunks(chunks)
    if not encoded_chunks:
        raise ValueError('chunks must not be empty')

    vector_size = len(encoded_chunks[0]['dense'])
    collection = collection_definition(vector_size=vector_size, collection_name=collection_name)
    qdrant_ops.ensure_collection(collection)

    points = []
    for index, chunk in enumerate(chunks):
        payload = build_payload(
            document_id=document_id,
            document_key=document_key,
            version_id=version_id,
            version_no=version_no,
            chunk_index=index,
            text=chunk,
            is_latest=True,
            is_active=True,
        )
        points.append(
            build_hybrid_point_struct(
                point_id=payload['chunk_id'],
                dense_vector=encoded_chunks[index]['dense'],
                sparse_vector=encoded_chunks[index]['sparse'],
                payload=payload,
            )
        )

    qdrant_ops.upsert_points(points)

    encoded_query = runtime.encode_query(query)
    dense_hits = qdrant_ops.query_dense(encoded_query['dense'], limit=5)
    sparse_hits = qdrant_ops.query_sparse(encoded_query['sparse'], limit=5)

    return build_live_summary(
        collection=collection,
        points=points,
        dense_hits=dense_hits,
        sparse_hits=sparse_hits,
    )


def build_runtime_from_args(args):
    config = FastEmbedAdapterConfig(
        dense_model=args.dense_model,
        sparse_model=args.sparse_model,
        cache_dir=args.cache_dir,
        threads=args.threads,
    )
    return FastEmbedRuntimeFactory().create(config)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run live FastEmbed + Qdrant hybrid smoke path')
    parser.add_argument('--qdrant-url', default='http://localhost:6333')
    parser.add_argument('--collection-name', default='documents_live_hybrid')
    parser.add_argument('--dense-model', default='BAAI/bge-small-en-v1.5')
    parser.add_argument('--sparse-model', default='Qdrant/bm25')
    parser.add_argument('--cache-dir', default=None)
    parser.add_argument('--threads', type=int, default=None)
    parser.add_argument('--document-id', default='live-doc')
    parser.add_argument('--document-key', default='live:doc')
    parser.add_argument('--version-id', default=None)
    parser.add_argument('--query', required=True)
    parser.add_argument('--chunk', action='append', dest='chunks', required=True)
    args = parser.parse_args(argv)

    runtime = build_runtime_from_args(args)
    client = QdrantClientFactory(url=args.qdrant_url).create()
    qdrant_ops = LiveHybridQdrantOps(client, collection_name=args.collection_name)
    summary = run_live_hybrid(
        chunks=args.chunks,
        query=args.query,
        version_id=args.version_id or 'live-%s' % uuid4().hex[:12],
        document_id=args.document_id,
        document_key=args.document_key,
        runtime=runtime,
        qdrant_ops=qdrant_ops,
        collection_name=args.collection_name,
    )
    print(json.dumps(summary, ensure_ascii=False, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
