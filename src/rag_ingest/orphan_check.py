def find_orphan_point_ids(db_point_ids, qdrant_point_ids):
    return sorted(list(set(qdrant_point_ids) - set(db_point_ids)))
