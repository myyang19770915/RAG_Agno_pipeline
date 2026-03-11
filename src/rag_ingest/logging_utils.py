from datetime import datetime


def build_log_event(event, **kwargs):
    payload = {'event': event, 'timestamp': datetime.utcnow().isoformat() + 'Z'}
    payload.update(kwargs)
    return payload
