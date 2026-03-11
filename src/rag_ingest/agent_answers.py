from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentAnswer:
    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    used_chunks_count: int = 0
    confidence: float | None = None
    notes: str | None = None
