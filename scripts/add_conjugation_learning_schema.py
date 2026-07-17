#!/usr/bin/env python3
"""Add graph-native conjugation learning groups and tense metadata."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def add_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row[1] for row in db.execute(f'PRAGMA table_info({table})')}
    if column not in columns:
        db.execute(f'ALTER TABLE {table} ADD COLUMN {definition}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.executescript("""
        INSERT OR IGNORE INTO object_types(code,label,description) VALUES
          ('learning_group','Learning group','A pedagogical sequence of related learning objects.'),
          ('conjugation_tense','Conjugation tense','A named, reusable tense or conjugation target.');
        INSERT OR IGNORE INTO relationship_types(code,label,is_directional,description) VALUES
          ('realizes_tense','Realizes tense',1,'Links a verb-specific paradigm to its reusable tense object.'),
          ('explains_conjugation','Explains conjugation',1,'Links a verb to a structured conjugation explanation object.');
        CREATE TABLE IF NOT EXISTS conjugation_tense_metadata (
          object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE,
          learning_group_id TEXT NOT NULL REFERENCES language_objects(id),
          mood TEXT NOT NULL, tense TEXT NOT NULL, display_order INTEGER NOT NULL,
          cefr_recommendation TEXT, formation TEXT NOT NULL DEFAULT 'simple',
          explanation_object_id TEXT REFERENCES language_objects(id),
          usage_notes_object_id TEXT REFERENCES language_objects(id),
          featured_example_id TEXT REFERENCES language_objects(id),
          source_id TEXT REFERENCES sources(id), confidence REAL,
          review_status TEXT NOT NULL DEFAULT 'metadata_ready',
          UNIQUE(learning_group_id, display_order)
        );
        CREATE INDEX IF NOT EXISTS tense_metadata_by_group
          ON conjugation_tense_metadata(learning_group_id, display_order);
    """)
    add_column(db, 'verb_metadata', 'explanation_object_id', 'explanation_object_id TEXT REFERENCES language_objects(id)')
    add_column(db, 'verb_metadata', 'usage_notes_object_id', 'usage_notes_object_id TEXT REFERENCES language_objects(id)')
    db.execute("INSERT INTO metadata(key,value) VALUES ('schema_version','6') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
    db.execute("INSERT INTO metadata(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('conjugation_learning_model', 'Learning groups contain reusable tense objects; verb paradigms realize those tense objects.'))
    db.commit()
    print('Conjugation learning schema ready.')


if __name__ == '__main__':
    main()
