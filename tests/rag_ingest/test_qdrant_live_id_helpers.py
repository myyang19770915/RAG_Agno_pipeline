from rag_ingest.qdrant_payloads import build_qdrant_point_id


def test_build_qdrant_point_id_is_deterministic_uuid_string():
    a = build_qdrant_point_id('ver_001', 0)
    b = build_qdrant_point_id('ver_001', 0)
    c = build_qdrant_point_id('ver_001', 1)
    assert a == b
    assert a != c
    assert len(a) == 36
