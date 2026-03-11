from rag_ingest.query_encoders import RuntimeQueryEncoder


class FakeRuntime:
    def encode_query(self, text):
        return {
            'dense': [0.1, 0.2],
            'sparse': {'indices': [1], 'values': [0.7]},
        }


def test_runtime_query_encoder_wraps_runtime_output_as_encoded_query():
    encoder = RuntimeQueryEncoder(FakeRuntime())
    encoded = encoder.encode('reset password')
    assert encoded.text == 'reset password'
    assert encoded.dense == [0.1, 0.2]
    assert encoded.sparse['indices'] == [1]
