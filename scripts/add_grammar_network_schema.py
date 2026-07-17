#!/usr/bin/env python3
"""Add grammar taxonomy and parser matching extension points.

No grammar inventory is seeded here. This migration only makes existing and
future Grammar Language Objects consistently classifiable and matchable.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path


MIGRATION_ID = "20260717_grammar_network_schema"

SCHEMA = """
INSERT OR IGNORE INTO object_types(code,label,description) VALUES
  ('grammar_topic','Grammar topic','A broad navigational grouping for Grammar Language Objects.');
INSERT OR IGNORE INTO relationship_types(code,label,is_directional,description) VALUES
  ('triggers_grammar','Triggers grammar',1,'Links a lexical expression or construction to a grammar object it licenses or triggers.'),
  ('contrasts_with','Contrasts with',0,'Links two grammar objects intended for comparison.'),
  ('requires','Requires',1,'Links a grammar object to a prerequisite or required grammar object.'),
  ('governs_agreement','Governs agreement',1,'Links an agreement rule to the objects or forms governed by it.'),
  ('belongs_to_grammar_topic','Belongs to grammar topic',1,'Places a grammar object within a broad grammar-topic object.');
CREATE TABLE IF NOT EXISTS grammar_categories (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS grammar_metadata (
  canonical_object_id TEXT PRIMARY KEY REFERENCES canonical_objects(canonical_id) ON DELETE RESTRICT,
  category_code TEXT NOT NULL REFERENCES grammar_categories(code),
  pedagogical_order INTEGER,
  analysis_priority INTEGER NOT NULL DEFAULT 100,
  is_sentence_detectable INTEGER NOT NULL DEFAULT 1 CHECK(is_sentence_detectable IN (0,1)),
  review_status TEXT NOT NULL DEFAULT 'metadata_ready'
);
CREATE TRIGGER IF NOT EXISTS validate_grammar_metadata_object_type
BEFORE INSERT ON grammar_metadata
WHEN (SELECT object_type_code FROM canonical_objects WHERE canonical_id = NEW.canonical_object_id)
     NOT IN ('grammar_construction','conjugation_tense','sentence_pattern','grammar_topic')
BEGIN
  SELECT RAISE(ABORT, 'Grammar metadata requires a Grammar Language Object');
END;
CREATE INDEX IF NOT EXISTS idx_grammar_metadata_category
  ON grammar_metadata(category_code, pedagogical_order);
CREATE INDEX IF NOT EXISTS idx_grammar_metadata_detection
  ON grammar_metadata(is_sentence_detectable, analysis_priority);
"""

CATEGORIES = [
    ("verb_tense", "Verb tense", "A named tense or temporal verb system."),
    ("verb_mood", "Verb mood", "A named grammatical mood."),
    ("verb_construction", "Verb construction", "A reusable verb or auxiliary construction."),
    ("clause_structure", "Clause structure", "A clause-level or sentence-structure rule."),
    ("pronoun_system", "Pronoun system", "A pronoun selection, placement, or reference rule."),
    ("agreement", "Agreement", "A gender, number, person, or participle agreement rule."),
    ("negation", "Negation", "A negation construction or rule."),
    ("interrogation", "Interrogation", "A question-building construction or rule."),
    ("determiner", "Determiner", "An article, determiner, or related selection rule."),
    ("word_order", "Word order", "A constituent-order or placement rule."),
    ("orthography", "Orthography", "A spelling, elision, or written-form rule."),
]

MATCH_TABLE = """
CREATE TABLE sentence_analysis_object_matches_v2 (
  id TEXT PRIMARY KEY,
  analysis_id TEXT NOT NULL REFERENCES sentence_analysis_instances(id) ON DELETE CASCADE,
  node_id TEXT REFERENCES sentence_analysis_nodes(id) ON DELETE SET NULL,
  canonical_object_id TEXT REFERENCES canonical_objects(canonical_id) ON DELETE RESTRICT,
  surface_text TEXT NOT NULL,
  start_offset INTEGER,
  end_offset INTEGER,
  match_role TEXT NOT NULL CHECK(match_role IN (
    'lemma','inflected_form','contraction_component','expression','collocation',
    'grammar_object','sentence_target','unknown'
  )),
  resolution_status TEXT NOT NULL CHECK(resolution_status IN ('resolved','ambiguous','unresolved')),
  engine_kind TEXT NOT NULL CHECK(engine_kind IN ('deterministic','ai_assisted','hybrid')),
  confidence REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def upgrade_analysis_match_role(db: sqlite3.Connection) -> None:
    row = db.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='sentence_analysis_object_matches'"
    ).fetchone()
    if row is None or "'grammar_object'" in row[0]:
        return
    db.executescript(MATCH_TABLE)
    db.execute(
        """INSERT INTO sentence_analysis_object_matches_v2
           SELECT id,analysis_id,node_id,canonical_object_id,surface_text,start_offset,end_offset,
                  CASE WHEN match_role='grammar_construction' THEN 'grammar_object' ELSE match_role END,
                  resolution_status,engine_kind,confidence,created_at
           FROM sentence_analysis_object_matches"""
    )
    db.execute("DROP TABLE sentence_analysis_object_matches")
    db.execute("ALTER TABLE sentence_analysis_object_matches_v2 RENAME TO sentence_analysis_object_matches")
    db.execute("CREATE INDEX idx_analysis_matches_analysis_span ON sentence_analysis_object_matches(analysis_id, start_offset, end_offset)")
    db.execute("CREATE INDEX idx_analysis_matches_canonical_object ON sentence_analysis_object_matches(canonical_object_id)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    upgrade_analysis_match_role(db)
    checksum = hashlib.sha256((SCHEMA + MATCH_TABLE).encode()).hexdigest()
    db.execute(
        "INSERT OR IGNORE INTO schema_migrations(id,checksum,description) VALUES (?,?,?)",
        (MIGRATION_ID, checksum, "Grammar taxonomy, semantic relationship types, and generic grammar-object analysis matches."),
    )
    db.executemany(
        "INSERT OR IGNORE INTO grammar_categories(code,label,description) VALUES (?,?,?)",
        CATEGORIES,
    )
    db.execute(
        """INSERT INTO metadata(key,value) VALUES (?,?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        ("grammar_network_model", "Grammar Language Objects use grammar_metadata and typed graph relationships; sentence analysis may match grammar objects but never creates them."),
    )
    db.commit()
    print("Grammar network schema is ready; no grammar inventory was imported.")


if __name__ == "__main__":
    main()
