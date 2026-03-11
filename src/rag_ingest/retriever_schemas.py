from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrieveRequest:
    query: str
    top_k: int = 5
    filters: dict[str, Any] = field(default_factory=dict)
    rewrite_mode: str = "none"
    history_mode: bool = False
    include_debug: bool = False


@dataclass
class RetrieveResult:
    text: str
    score: float
    document_key: str
    version_id: str
    chunk_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    citation: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrieveResponse:
    results: list[RetrieveResult]
    applied_query: str
    applied_queries: list[str]
    retrieval_mode: str
    debug: dict[str, Any] | None = None
