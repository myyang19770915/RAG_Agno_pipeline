from datetime import datetime

from rag_ingest.observability import build_event, timed_call


def test_timed_call_returns_result_and_metadata():
    result, metadata = timed_call('sample-operation', lambda: 'ok')

    assert result == 'ok'
    assert metadata['label'] == 'sample-operation'
    assert isinstance(metadata['elapsed_ms'], float)


def test_timed_call_reports_non_negative_elapsed_ms():
    _, metadata = timed_call('fast-op', lambda: None)

    assert metadata['elapsed_ms'] >= 0.0



def test_build_event_returns_event_timestamp_and_fields():
    event = build_event('retrieval.completed', query='reset password', top_k=5)

    assert event['event'] == 'retrieval.completed'
    assert event['query'] == 'reset password'
    assert event['top_k'] == 5
    assert isinstance(event['timestamp'], str)
    datetime.fromisoformat(event['timestamp'])
