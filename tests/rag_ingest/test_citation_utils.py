from rag_ingest.citation_utils import build_citation, format_retrieve_result


def test_build_citation_keeps_full_trace_fields():
    citation = build_citation("sharepoint:SOP-001", "ver_3", "ver_3:0007")
    assert citation == {
        "document_key": "sharepoint:SOP-001",
        "version_id": "ver_3",
        "chunk_id": "ver_3:0007",
    }


def test_format_retrieve_result_outputs_standard_contract():
    result = format_retrieve_result(
        text="Reset password from settings",
        score=0.82,
        document_key="sharepoint:SOP-001",
        version_id="ver_3",
        chunk_id="ver_3:0007",
        metadata={"source_system": "sharepoint"},
    )
    assert result.document_key == "sharepoint:SOP-001"
    assert result.citation["chunk_id"] == "ver_3:0007"
