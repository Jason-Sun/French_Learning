from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Token:
    surface: str
    normalized: str
    start: int
    end: int
    underlying: list[str] = field(default_factory=list)
    object_id: str | None = None
    lemma_id: str | None = None
    confidence: float = 0.0
    source: str = "deterministic"


@dataclass
class AnalysisNode:
    id: str
    type: str
    label: str
    object_id: str | None = None
    span: tuple[int, int] | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "deterministic"
    confidence: float = 1.0


@dataclass
class AnalysisEdge:
    source: str
    target: str
    type: str
    confidence: float = 1.0


@dataclass
class SentenceAnalysis:
    id: str
    sentence: str
    normalized_sentence: str
    engine_version: str
    tokens: list[Token]
    nodes: list[AnalysisNode]
    edges: list[AnalysisEdge]
    learning: dict[str, Any]
    unknown_tokens: list[str]
    provenance: str = "deterministic"
    confidence: float = 1.0
    cache_status: str = "transient"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
