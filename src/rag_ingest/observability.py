from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable


def build_event(name: str, **fields: Any) -> dict[str, Any]:
    return {
        'event': name,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        **fields,
    }


def timed_call(label: str, fn: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    started_at = perf_counter()
    result = fn()
    elapsed_ms = (perf_counter() - started_at) * 1000.0
    return result, {'label': label, 'elapsed_ms': elapsed_ms}
