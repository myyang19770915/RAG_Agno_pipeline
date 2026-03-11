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
