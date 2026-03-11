def retry_operation(fn, retries=3, allowed_exceptions=(Exception,)):
    last_error = None
    for _ in range(retries):
        try:
            return fn()
        except allowed_exceptions as exc:
            last_error = exc
    raise last_error
