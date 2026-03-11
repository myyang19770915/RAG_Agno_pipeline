from rag_ingest.document_encoders import RuntimeDocumentEncoder
from rag_ingest.hybrid_ingest_orchestrator import prepare_hybrid_chunk_vectors
from rag_ingest.query_encoders import RuntimeQueryEncoder
from rag_ingest.qdrant_retriever_backend import QdrantRetrieverBackend
from rag_ingest.retriever_tool import retrieve_tool
from rag_ingest.services.ingest_pipeline import FakeQdrant, ingest_document
from rag_ingest.db.session import InMemorySession


class FakeRuntime:
    def encode_query(self, text):
        return {'dense': [0.1, 0.2], 'sparse': {'indices': [1], 'values': [0.7]}}

    def encode_chunks(self, chunks):
        return [
            {'dense': [0.1, 0.2], 'sparse': {'indices': [1], 'values': [0.8]}}
            for _ in chunks
        ]


class FakeClient:
    def __init__(self, points):
        self._points = points

    def search(self, **kwargs):
        results = []
        for point_id, point in self._points.items():
            payload = point['payload']
            if payload.get('is_latest') and payload.get('is_active'):
                results.append({'id': point_id, 'score': 0.9, 'payload': payload})
        return results[: kwargs.get('limit', 5)]



def test_end_to_end_hybrid_smoke_contract_keeps_tool_output_shape():
    runtime = FakeRuntime()
    document_encoder = RuntimeDocumentEncoder(runtime)
    query_encoder = RuntimeQueryEncoder(runtime)
    dense_vectors, sparse_vectors = prepare_hybrid_chunk_vectors(
        ['reset password policy'],
        document_encoder,
    )

    session = InMemorySession()
    qdrant = FakeQdrant()
    ingest_document(
        session,
        qdrant,
        {'document_key': 'doc1', 'version_fingerprint': 'fp1', 'source_system': 'smoke'},
        ['reset password policy'],
        dense_vectors,
        sparse_vectors=sparse_vectors,
    )

    backend = QdrantRetrieverBackend(client=FakeClient(qdrant.points), query_encoder=query_encoder)
    response = retrieve_tool({'query': 'reset password', 'top_k': 1}, backend=backend)

    assert response['results'][0]['document_key'] == 'doc1'
    assert response['results'][0]['citation']['chunk_id']
