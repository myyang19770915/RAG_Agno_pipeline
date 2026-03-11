from rag_ingest.contracts import build_document_key, build_version_fingerprint


def test_build_document_key_prefers_business_id():
    key = build_document_key(source_system="sharepoint", business_id="SOP-001", normalized_path="/a/b.pdf")
    assert key == "sharepoint:SOP-001"


def test_build_document_key_falls_back_to_path():
    key = build_document_key(source_system="sharepoint", business_id=None, normalized_path="/qa/sop-001.pdf")
    assert key == "sharepoint:/qa/sop-001.pdf"


def test_build_version_fingerprint_changes_when_hash_changes():
    a = build_version_fingerprint(file_hash="aaa", file_size=100, modified_ts="2026-03-11T00:00:00Z", text_hash="txt1")
    b = build_version_fingerprint(file_hash="bbb", file_size=100, modified_ts="2026-03-11T00:00:00Z", text_hash="txt1")
    assert a != b
