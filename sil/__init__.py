"""Sentence Intelligence Layer: framework-neutral French sentence analysis."""

from .engine import SentenceIntelligenceEngine
from .sqlite_repository import SQLiteKnowledgeRepository

__all__ = ["SentenceIntelligenceEngine", "SQLiteKnowledgeRepository"]
