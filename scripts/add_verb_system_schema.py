#!/usr/bin/env python3
"""Add graph-native conjugation realizations and deterministic teaching resources."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.executescript("""
      INSERT OR IGNORE INTO object_types(code,label,description) VALUES
        ('conjugation_realization','Conjugation realization','A person-specific simple, compound, or periphrastic realization built from Language Objects.');
      INSERT OR IGNORE INTO relationship_types(code,label,is_directional,description) VALUES
        ('explains','Explains',1,'Links a structured learning resource to the Language Object it explains.');
      CREATE TABLE IF NOT EXISTS conjugation_realizations (
        object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE,
        paradigm_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
        realization_type TEXT NOT NULL CHECK(realization_type IN ('simple','compound','periphrastic')),
        person TEXT, number TEXT, source_id TEXT REFERENCES sources(id),
        confidence REAL, review_status TEXT NOT NULL DEFAULT 'draft',
        UNIQUE(paradigm_id, person, number)
      );
      CREATE INDEX IF NOT EXISTS conjugation_realizations_by_paradigm
        ON conjugation_realizations(paradigm_id, person, number);
      CREATE TABLE IF NOT EXISTS conjugation_realization_components (
        realization_id TEXT NOT NULL REFERENCES conjugation_realizations(object_id) ON DELETE CASCADE,
        position INTEGER NOT NULL, role_code TEXT NOT NULL,
        object_id TEXT NOT NULL REFERENCES language_objects(id),
        PRIMARY KEY(realization_id, position)
      );
      CREATE TABLE IF NOT EXISTS teaching_guidance (
        resource_object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE,
        why_en TEXT, formation_en TEXT, common_mistakes_json TEXT NOT NULL DEFAULT '[]',
        related_object_ids_json TEXT NOT NULL DEFAULT '[]', source_id TEXT REFERENCES sources(id),
        confidence REAL, review_status TEXT NOT NULL DEFAULT 'draft'
      );
    """)
    db.execute("INSERT INTO metadata(key,value) VALUES ('schema_version','7') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
    db.execute("INSERT INTO metadata(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('verb_system_model', 'Conjugation realizations are Language Objects composed from ordered Language Object components; teaching resources explain canonical objects.'))
    db.commit()
    print('Verb system schema ready.')


if __name__ == '__main__':
    main()
