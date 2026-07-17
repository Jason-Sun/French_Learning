from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SQLiteKnowledgeRepository:
    """SQLite adapter; the engine depends only on this small read interface."""

    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row

    def objects(self, normalized: str) -> list[dict]:
        return [dict(row) for row in self.db.execute("SELECT * FROM language_objects WHERE normalized_form=?", (normalized,))]

    def forms(self, normalized: str) -> list[dict]:
        return [dict(row) for row in self.db.execute("""SELECT f.*, lemma.id AS lemma_id, lemma.canonical_form AS lemma, x.mood, x.tense, x.person, x.number
            FROM language_objects f JOIN form_features x ON x.object_id=f.id
            JOIN relationships r ON r.source_object_id=f.id AND r.relationship_type_code='inflected_form_of'
            JOIN language_objects lemma ON lemma.id=r.target_object_id WHERE f.normalized_form=?""", (normalized,))]

    def grammar(self, name: str) -> dict | None:
        row = self.db.execute("SELECT * FROM language_objects WHERE type_code='grammar_construction' AND normalized_form=?", (name.casefold(),)).fetchone()
        return dict(row) if row else None

    def relationship(self, source_id: str, relation: str, target_id: str) -> bool:
        return bool(self.db.execute("SELECT 1 FROM relationships WHERE source_object_id=? AND relationship_type_code=? AND target_object_id=?", (source_id, relation, target_id)).fetchone())

    def persist_analysis(self, analysis) -> None:
        """Persist an analysis instance without promoting it to global knowledge."""
        payload = analysis.to_dict()
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO sentence_analysis_instances (id,sentence,normalized_sentence,engine_version,provenance,confidence,cache_status) VALUES (?,?,?,?,?,?,?)", (analysis.id, analysis.sentence, analysis.normalized_sentence, analysis.engine_version, analysis.provenance, analysis.confidence, analysis.cache_status))
            self.db.execute("DELETE FROM sentence_analysis_nodes WHERE analysis_id=?", (analysis.id,))
            self.db.execute("DELETE FROM sentence_analysis_edges WHERE analysis_id=?", (analysis.id,))
            self.db.execute("DELETE FROM sentence_learning_items WHERE analysis_id=?", (analysis.id,))
            self.db.executemany("INSERT INTO sentence_analysis_nodes VALUES (?,?,?,?,?,?,?,?,?,?)", [(node.id, analysis.id, node.type, node.object_id, node.label, node.span[0] if node.span else None, node.span[1] if node.span else None, json.dumps(node.payload), node.source, node.confidence) for node in analysis.nodes])
            self.db.executemany("INSERT INTO sentence_analysis_edges VALUES (?,?,?,?,?)", [(analysis.id, edge.source, edge.target, edge.type, edge.confidence) for edge in analysis.edges])
            for kind, values in analysis.learning.items():
                for value in values if isinstance(values, list) else [values]:
                    object_id = value if isinstance(value, str) and value.startswith('fr:') else None
                    self.db.execute("INSERT OR REPLACE INTO sentence_learning_items VALUES (?,?,?,?,?,?)", (analysis.id, object_id, kind, json.dumps(value), 'deterministic', analysis.confidence))
