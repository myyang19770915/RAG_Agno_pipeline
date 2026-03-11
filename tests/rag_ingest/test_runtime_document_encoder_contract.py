from rag_ingest.document_encoders import RuntimeDocumentEncoder


class FakeRuntime:
    def encode_chunks(self, chunks):
        return [
            {'dense': [0.1, 0.2], 'sparse': {'indices': [1], 'values': [0.8]}}
            for _ in chunks
        ]


def test_runtime_document_encoder_wraps_runtime_chunk_outputs():
    encoder = RuntimeDocumentEncoder(FakeRuntime())
    encoded = encoder.encode_chunks(['reset password'])
    assert encoded[0]['dense'] == [0.1, 0.2]
    assert encoded[0]['sparse']['indices'] == [1]
