from rag_ingest.qdrant_integration import collection_definition, payload_index_fields, latest_active_query_filter, version_points_selector


def test_collection_definition_has_documents_name_and_vector_size():
    cfg = collection_definition(vector_size=1024)
    assert cfg['collection_name'] == 'documents'
    assert cfg['vector_size'] == 1024


def test_payload_index_fields_include_version_and_status_keys():
    fields = payload_index_fields()
    assert 'document_key' in fields
    assert 'version_id' in fields
    assert 'is_latest' in fields
    assert 'is_active' in fields


def test_latest_active_query_filter_contains_both_flags():
    f = latest_active_query_filter()
    keys = [x['key'] for x in f['must']]
    assert 'is_latest' in keys
    assert 'is_active' in keys


def test_version_points_selector_filters_by_version_id():
    selector = version_points_selector('ver_001')
    assert selector['must'][0]['key'] == 'version_id'
    assert selector['must'][0]['match']['value'] == 'ver_001'
