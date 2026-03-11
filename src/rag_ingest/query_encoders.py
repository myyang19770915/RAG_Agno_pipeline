from dataclasses import dataclass


@dataclass
class EncodedQuery:
    text: str
    dense: list | None = None
    sparse: dict | None = None


class BaseQueryEncoder:
    def encode(self, text: str) -> EncodedQuery:
        raise NotImplementedError

    def encode_dense(self, text: str):
        return self.encode(text).dense

    def encode_sparse(self, text: str):
        return self.encode(text).sparse


class StaticQueryEncoder(BaseQueryEncoder):
    def __init__(self, dense_vector=None, sparse_vector=None):
        self._dense_vector = dense_vector
        self._sparse_vector = sparse_vector

    def encode(self, text: str) -> EncodedQuery:
        return EncodedQuery(
            text=text,
            dense=self._dense_vector,
            sparse=self._sparse_vector,
        )


class RuntimeQueryEncoder(BaseQueryEncoder):
    def __init__(self, runtime):
        self._runtime = runtime

    def encode(self, text: str) -> EncodedQuery:
        encoded = self._runtime.encode_query(text)
        return EncodedQuery(
            text=text,
            dense=encoded.get('dense'),
            sparse=encoded.get('sparse'),
        )


class SplitQueryEncoder(BaseQueryEncoder):
    def __init__(self, dense_encoder, sparse_encoder):
        self._dense_encoder = dense_encoder
        self._sparse_encoder = sparse_encoder

    def encode(self, text: str) -> EncodedQuery:
        return EncodedQuery(
            text=text,
            dense=self._dense_encoder.encode_dense(text),
            sparse=self._sparse_encoder.encode_sparse(text),
        )


class EmbeddingProviderDenseEncoder(object):
    def __init__(self, embedding_provider):
        self._embedding_provider = embedding_provider

    def encode_dense(self, text: str):
        return self._embedding_provider.embed_texts([text])[0]


class SparseFastEmbedEncoder(object):
    def __init__(self, sparse_model):
        self._sparse_model = sparse_model

    def encode_sparse(self, text: str):
        value = next(iter(self._sparse_model.query_embed([text])))
        if isinstance(value, dict):
            return {
                'indices': list(value.get('indices', [])),
                'values': list(value.get('values', [])),
            }
        return {
            'indices': list(getattr(value, 'indices', [])),
            'values': list(getattr(value, 'values', [])),
        }
