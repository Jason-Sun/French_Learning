#!/usr/bin/env python3
"""Add first-class lexical senses without replacing the legacy definition adapter."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path


MIGRATION_ID = "20260717_lexical_sense_schema"

SCHEMA = """
INSERT OR IGNORE INTO object_types(code,label,description) VALUES
  ('lexical_sense','Lexical sense','A distinct evidenced meaning of a lexical Language Object.');
INSERT OR IGNORE INTO relationship_types(code,label,is_directional,description) VALUES
  ('has_sense','Has sense',1,'Links a lexical Language Object to one of its distinct lexical senses.');
INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES
  ('english_gloss','text','English gloss','An evidence-backed English translation or gloss for a lexical sense.');
CREATE TABLE IF NOT EXISTS lexical_senses (
  sense_object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE RESTRICT,
  owner_canonical_id TEXT NOT NULL REFERENCES canonical_objects(canonical_id) ON DELETE RESTRICT,
  part_of_speech TEXT NOT NULL,
  semantic_key TEXT NOT NULL,
  display_order INTEGER NOT NULL,
  lifecycle TEXT NOT NULL DEFAULT 'canonical',
  UNIQUE(owner_canonical_id, semantic_key)
);
CREATE INDEX IF NOT EXISTS idx_lexical_senses_owner_order
  ON lexical_senses(owner_canonical_id, display_order, sense_object_id);
CREATE TRIGGER IF NOT EXISTS validate_lexical_sense_object_type
BEFORE INSERT ON lexical_senses
WHEN (SELECT type_code FROM language_objects WHERE id = NEW.sense_object_id) <> 'lexical_sense'
BEGIN
  SELECT RAISE(ABORT, 'lexical_senses requires a lexical_sense Language Object');
END;
CREATE TRIGGER IF NOT EXISTS validate_lexical_sense_owner_type
BEFORE INSERT ON lexical_senses
WHEN (SELECT object_type_code FROM canonical_objects WHERE canonical_id = NEW.owner_canonical_id) <> 'word'
BEGIN
  SELECT RAISE(ABORT, 'lexical sense owner must be a word canonical object');
END;
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()

    database = sqlite3.connect(args.database)
    database.execute("PRAGMA foreign_keys=ON")
    database.executescript(SCHEMA)
    checksum = hashlib.sha256(SCHEMA.encode()).hexdigest()
    database.execute(
        """INSERT OR IGNORE INTO schema_migrations(id, checksum, description)
           VALUES (?, ?, ?)""",
        (
            MIGRATION_ID,
            checksum,
            "First-class lexical sense objects, semantic ordering, and independently evidenced English glosses.",
        ),
    )
    database.execute(
        """INSERT INTO metadata(key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        (
            "lexical_sense_model",
            "A lexical sense is a canonical Language Object linked from its word by has_sense; its gloss facts are independently evidenced.",
        ),
    )
    database.commit()
    print("Lexical sense schema is ready; no senses were imported.")


if __name__ == "__main__":
    main()
