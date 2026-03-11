class BaseDocumentEncoder:
    def encode_chunks(self, chunks):
        raise NotImplementedError


class StaticDocumentEncoder(BaseDocumentEncoder):
    def __init__(self, dense_vectors=None, sparse_vectors=None):
        self._dense_vectors = dense_vectors or []
        self._sparse_vectors = sparse_vectors or []

    def encode_chunks(self, chunks):
        encoded = []
        for index, _chunk in enumerate(chunks):
            encoded.append(
                {
                    'dense': self._dense_vectors[index] if index < len(self._dense_vectors) else None,
                    'sparse': self._sparse_vectors[index] if index < len(self._sparse_vectors) else None,
                }
            )
        return encoded


class RuntimeDocumentEncoder(BaseDocumentEncoder):
    def __init__(self, runtime):
        self._runtime = runtime

    def encode_chunks(self, chunks):
        return self._runtime.encode_chunks(chunks)
