from datetime import datetime, timedelta


def cleanup_inactive_versions(session, qdrant, retention_days=7):
    deleted = 0
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    for version in session.versions:
        if version.status == 'superseded' and version.ingested_at <= cutoff:
            deleted += qdrant.delete_inactive_version(version.version_id)
            version.status = 'deleted'
            version.deleted_at = datetime.utcnow()
    return deleted
