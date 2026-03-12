from datetime import datetime

from rag_ingest.observability import build_event, render_event_json, timed_call


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
    assert event['level'] == 'info'
    assert isinstance(event['timestamp'], str)
    datetime.fromisoformat(event['timestamp'])


def test_build_event_includes_operation_metadata_when_supplied():
    event = build_event(
        'ingest.completed',
        operation='ingest',
        status='ok',
        timing={'elapsed_ms': 12.5},
        summary={'documents_indexed': 3},
    )

    assert event['operation'] == 'ingest'
    assert event['status'] == 'ok'
    assert event['timing'] == {'elapsed_ms': 12.5}
    assert event['summary'] == {'documents_indexed': 3}


def test_render_event_json_returns_stable_operator_shape():
    rendered = render_event_json(
        build_event(
            'retrieval.completed',
            operation='retrieve',
            status='ok',
            timing={'elapsed_ms': 9.1},
            summary={'results': 2},
        )
    )

    assert rendered.endswith('\n')
    assert '"event": "retrieval.completed"' in rendered
    assert '"operation": "retrieve"' in rendered
    assert '"elapsed_ms": 9.1' in rendered
