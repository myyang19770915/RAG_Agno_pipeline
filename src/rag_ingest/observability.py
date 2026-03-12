from __future__ import annotations

from time import perf_counter
from typing import Any, Callable


def timed_call(label: str, fn: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    started_at = perf_counter()
    result = fn()
    elapsed_ms = (perf_counter() - started_at) * 1000.0
    return result, {'label': label, 'elapsed_ms': elapsed_ms}
