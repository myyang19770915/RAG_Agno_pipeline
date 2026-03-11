def filter_candidates(candidates, history_mode=False, extra_filters=None):
    """Filter retrieval candidates by active/latest flags and optional metadata filters."""
    extra_filters = extra_filters or {}
    filtered = []

    for candidate in candidates:
        if candidate.get('is_active') is not True:
            continue
        if not history_mode and candidate.get('is_latest') is not True:
            continue

        metadata = candidate.get('metadata') or {}
        if any(
            candidate.get(key, metadata.get(key)) != value
            for key, value in extra_filters.items()
        ):
            continue

        filtered.append(candidate)

    return filtered
