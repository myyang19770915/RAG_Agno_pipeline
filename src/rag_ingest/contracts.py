import hashlib


def build_document_key(source_system, business_id, normalized_path):
    if business_id:
        return "%s:%s" % (source_system, business_id)
    return "%s:%s" % (source_system, normalized_path)


def build_version_fingerprint(file_hash, file_size, modified_ts, text_hash):
    raw = "%s|%s|%s|%s" % (file_hash, file_size, modified_ts, text_hash)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
