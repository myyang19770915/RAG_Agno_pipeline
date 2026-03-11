from rag_ingest.qdrant_retriever_backend import build_dense_query_args, build_sparse_query_args


def test_build_dense_query_args_targets_named_dense_vector():
    args = build_dense_query_args([0.1, 0.2], limit=5)
    assert args['query_vector'][0] == 'dense'
    assert args['limit'] == 5


def test_build_sparse_query_args_targets_named_sparse_vector():
    args = build_sparse_query_args({'indices': [1], 'values': [0.7]}, limit=3)
    assert args['query_vector'][0] == 'sparse'
    assert args['limit'] == 3
