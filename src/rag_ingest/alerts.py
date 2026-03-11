def find_stale_active_versions(session, now, max_age_days=30):
    alerts = []
    for version in session.versions:
        if version.status != 'active':
            continue
        age_days = (now - version.ingested_at).days
        if age_days > max_age_days:
            alerts.append(
                {
                    'version_id': version.version_id,
                    'document_id': version.document_id,
                    'age_days': age_days,
                    'severity': 'warning',
                    'message': 'active version is stale',
                }
            )
    return alerts
