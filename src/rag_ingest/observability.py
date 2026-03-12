from __future__ import annotations

import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable


_EVENT_VERSION = 1


def build_event(name: str, level: str = 'info', **fields: Any) -> dict[str, Any]:
    return {
        'event': name,
        'level': level,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_version': _EVENT_VERSION,
        **fields,
    }


def render_event_json(event: dict[str, Any]) -> str:
    return json.dumps(event, ensure_ascii=False, sort_keys=True) + '\n'


def timed_call(label: str, fn: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    started_at = perf_counter()
    result = fn()
    elapsed_ms = (perf_counter() - started_at) * 1000.0
    return result, {
        'label': label,
        'elapsed_ms': elapsed_ms,
    }
