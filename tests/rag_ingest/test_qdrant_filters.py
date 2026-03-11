from rag_ingest.qdrant_filters import latest_active_filter


def test_latest_active_filter_requires_latest_and_active():
    f = latest_active_filter()
    must = f['must']
    assert set([m['key'] for m in must]) == set(['is_latest', 'is_active'])
