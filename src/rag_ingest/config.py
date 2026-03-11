import os


def get_retention_days(default=7):
    value = os.environ.get('RAG_RETENTION_DAYS')
    if not value:
        return default
    return int(value)
