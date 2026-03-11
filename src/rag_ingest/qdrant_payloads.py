import uuid


def build_point_id(version_id, chunk_index):
    return '%s:%04d' % (version_id, chunk_index)


def build_qdrant_point_id(version_id, chunk_index):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, '%s:%04d' % (version_id, chunk_index)))


def build_payload(**kwargs):
    version_id = kwargs['version_id']
    chunk_index = kwargs['chunk_index']
    payload = dict(kwargs)
    payload['chunk_id'] = build_point_id(version_id, chunk_index)
    return payload
