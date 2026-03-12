from rag_ingest.observability import timed_call


def test_timed_call_returns_result_and_metadata():
    result, metadata = timed_call('sample-operation', lambda: 'ok')

    assert result == 'ok'
    assert metadata['label'] == 'sample-operation'
    assert isinstance(metadata['elapsed_ms'], float)


def test_timed_call_reports_non_negative_elapsed_ms():
    _, metadata = timed_call('fast-op', lambda: None)

    assert metadata['elapsed_ms'] >= 0.0
