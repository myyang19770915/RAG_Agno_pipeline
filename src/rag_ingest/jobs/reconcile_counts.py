class ReconcileResult(object):
    def __init__(self, status, db_count, qdrant_count):
        self.status = status
        self.db_count = db_count
        self.qdrant_count = qdrant_count


def reconcile_active_chunk_counts(session, qdrant, version_id):
    db_count = 0
    for version in session.versions:
        if version.version_id == version_id and version.status == 'active':
            db_count = version.chunk_count
            break
    qdrant_count = qdrant.count_version(version_id, active_only=True)
    status = 'matched' if db_count == qdrant_count else 'mismatch'
    return ReconcileResult(status, db_count, qdrant_count)


def reconcile_orphans(db_point_ids, qdrant_point_ids):
    orphans = sorted(list(set(qdrant_point_ids) - set(db_point_ids)))
    return {'orphans': orphans, 'status': 'ok' if not orphans else 'orphans_found'}
