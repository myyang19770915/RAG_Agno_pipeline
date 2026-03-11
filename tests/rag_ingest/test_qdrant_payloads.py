from rag_ingest.qdrant_payloads import build_point_id, build_payload


def test_point_id_is_version_and_chunk_index():
    assert build_point_id('ver_003', 7) == 'ver_003:0007'


def test_payload_marks_latest_and_active():
    payload = build_payload(document_id='doc_1', document_key='sharepoint:SOP-001', version_id='ver_3', version_no=3, chunk_index=7, is_latest=True, is_active=True)
    assert payload['is_latest'] is True
    assert payload['is_active'] is True
