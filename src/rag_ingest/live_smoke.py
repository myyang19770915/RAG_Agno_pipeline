from rag_ingest.document_encoders import StaticDocumentEncoder
from rag_ingest.hybrid_ingest_orchestrator import prepare_hybrid_chunk_vectors
from rag_ingest.qdrant_integration import collection_definition
from rag_ingest.qdrant_retriever_backend import (
    build_dense_query_args,
    build_sparse_query_args,
    normalize_qdrant_result,
)
from rag_ingest.query_encoders import StaticQueryEncoder


def build_smoke_payload(document_key, version_fingerprint, source_system='smoke'):
    return {
        'document_key': document_key,
        'version_fingerprint': version_fingerprint,
        'source_system': source_system,
    }



def summarize_hits(hits):
    return [
        {
            'chunk_id': hit.get('chunk_id'),
            'document_key': hit.get('document_key'),
            'score': hit.get('score'),
        }
        for hit in hits
    ]



def run_live_smoke(
    document_key,
    version_fingerprint,
    chunks,
    query,
    *,
    document_encoder=None,
    query_encoder=None,
    qdrant_client=None,
    collection_manager=None,
    collection_name='documents',
):
    payload = build_smoke_payload(document_key, version_fingerprint)
    document_encoder = document_encoder or StaticDocumentEncoder()
    query_encoder = query_encoder or StaticQueryEncoder()

    dense_vectors, sparse_vectors = prepare_hybrid_chunk_vectors(chunks, document_encoder)
    encoded_query = query_encoder.encode(query)

    vector_size = len(dense_vectors[0]) if dense_vectors and dense_vectors[0] is not None else 0
    collection = collection_definition(vector_size=vector_size, collection_name=collection_name)

    if collection_manager is not None:
        collection_manager.ensure_collection(collection)

    result = {
        'collection': collection,
        'payload': payload,
        'chunk_vectors': {
            'dense': dense_vectors,
            'sparse': sparse_vectors,
        },
        'dense_hits': [],
        'sparse_hits': [],
    }

    if qdrant_client is None:
        return result

    dense_hits = qdrant_client.search(
        collection_name=collection_name,
        **build_dense_query_args(encoded_query.dense, limit=5),
    )
    sparse_hits = qdrant_client.search(
        collection_name=collection_name,
        **build_sparse_query_args(encoded_query.sparse, limit=5),
    )

    result['dense_hits'] = summarize_hits([normalize_qdrant_result(hit) for hit in dense_hits])
    result['sparse_hits'] = summarize_hits([normalize_qdrant_result(hit) for hit in sparse_hits])
    return result
