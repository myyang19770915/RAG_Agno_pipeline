def latest_active_filter():
    return {
        'must': [
            {'key': 'is_latest', 'match': {'value': True}},
            {'key': 'is_active', 'match': {'value': True}},
        ]
    }


def filter_by_document_key(document_key):
    return {'must': [{'key': 'document_key', 'match': {'value': document_key}}]}


def filter_by_version_id(version_id):
    return {'must': [{'key': 'version_id', 'match': {'value': version_id}}]}


def history_mode_filter(document_key):
    return filter_by_document_key(document_key)
