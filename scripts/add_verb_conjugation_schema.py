#!/usr/bin/env python3
"""Add durable verb metadata and tense-paradigm support to the Liens graph."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS verb_metadata (
  object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE,
  verb_group_code TEXT,
  is_irregular INTEGER NOT NULL DEFAULT 0,
  future_stem TEXT,
  auxiliary_lemma_id TEXT REFERENCES language_objects(id),
  note_en TEXT,
  note_zh TEXT,
  source_id TEXT REFERENCES sources(id),
  provenance TEXT NOT NULL DEFAULT 'curated',
  confidence REAL,
  status TEXT NOT NULL DEFAULT 'metadata_ready',
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS verb_metadata_by_group
  ON verb_metadata(verb_group_code, is_irregular);
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.executescript(SCHEMA)
    db.execute(
        "INSERT INTO metadata(key,value) VALUES ('schema_version','5') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
    )
    db.execute(
        "INSERT INTO metadata(key,value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ('conjugation_model', 'Root conjugations contain first-class mood-tense paradigms; forms are members of a tense paradigm.'),
    )
    db.commit()
    print('Verb metadata and tense-paradigm schema ready.')


if __name__ == '__main__':
    main()
