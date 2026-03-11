from dataclasses import dataclass


@dataclass
class FastEmbedRuntime:
    dense_model: object
    sparse_model: object

    def encode_chunks(self, chunks):
        dense_vectors = list(self.dense_model.embed(chunks))
        sparse_vectors = [self._normalize_sparse_vector(item) for item in self.sparse_model.embed(chunks)]
        encoded = []
        for index, _chunk in enumerate(chunks):
            encoded.append(
                {
                    'dense': dense_vectors[index],
                    'sparse': sparse_vectors[index],
                }
            )
        return encoded

    def encode_query(self, text):
        dense = next(iter(self.dense_model.query_embed([text])))
        sparse = self._normalize_sparse_vector(next(iter(self.sparse_model.query_embed([text]))))
        return {
            'dense': dense,
            'sparse': sparse,
        }

    @staticmethod
    def _normalize_sparse_vector(value):
        if isinstance(value, dict):
            return {
                'indices': list(value.get('indices', [])),
                'values': list(value.get('values', [])),
            }
        return {
            'indices': list(getattr(value, 'indices', [])),
            'values': list(getattr(value, 'values', [])),
        }


class FastEmbedRuntimeFactory:
    def __init__(self, dense_model_cls=None, sparse_model_cls=None):
        self._dense_model_cls = dense_model_cls
        self._sparse_model_cls = sparse_model_cls

    def create(self, config):
        if not config.dense_model:
            raise ValueError('dense_model is required')
        if not config.sparse_model:
            raise ValueError('sparse_model is required')

        dense_model_cls = self._dense_model_cls
        sparse_model_cls = self._sparse_model_cls
        if dense_model_cls is None or sparse_model_cls is None:
            try:
                from fastembed import TextEmbedding, SparseTextEmbedding
            except Exception as exc:
                raise RuntimeError('fastembed package not installed') from exc
            dense_model_cls = dense_model_cls or TextEmbedding
            sparse_model_cls = sparse_model_cls or SparseTextEmbedding

        return FastEmbedRuntime(
            dense_model=self._build_model(
                dense_model_cls,
                model_name=config.dense_model,
                cache_dir=config.cache_dir,
                threads=config.threads,
                stage='dense',
            ),
            sparse_model=self._build_model(
                sparse_model_cls,
                model_name=config.sparse_model,
                cache_dir=config.cache_dir,
                threads=config.threads,
                stage='sparse',
            ),
        )

    @staticmethod
    def _build_model(model_cls, *, model_name, cache_dir=None, threads=None, stage='model'):
        kwargs = {'model_name': model_name}
        if cache_dir is not None:
            kwargs['cache_dir'] = cache_dir
        if threads is not None:
            kwargs['threads'] = threads
        try:
            return model_cls(**kwargs)
        except Exception as exc:
            raise RuntimeError('Failed to initialize FastEmbed %s model: %s' % (stage, model_name)) from exc


def build_fastembed_config(dense_model=None, sparse_model=None, cache_dir=None, threads=None):
    return {
        'dense_model': dense_model,
        'sparse_model': sparse_model,
        'cache_dir': cache_dir,
        'threads': threads,
    }


def build_runtime_factory_spec(config):
    return config.as_dict()


class FastEmbedAdapterConfig:
    def __init__(self, dense_model=None, sparse_model=None, cache_dir=None, threads=None):
        self.dense_model = dense_model
        self.sparse_model = sparse_model
        self.cache_dir = cache_dir
        self.threads = threads

    def as_dict(self):
        return build_fastembed_config(
            dense_model=self.dense_model,
            sparse_model=self.sparse_model,
            cache_dir=self.cache_dir,
            threads=self.threads,
        )
