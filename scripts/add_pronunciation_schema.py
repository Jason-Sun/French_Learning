#!/usr/bin/env python3
"""Add durable, object-linked pronunciation records to a Liens knowledge graph."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS pronunciations (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
  ipa TEXT,
  syllables_json TEXT NOT NULL DEFAULT '[]',
  stress_json TEXT NOT NULL DEFAULT '[]',
  variant_code TEXT,
  audio_source_uri TEXT,
  local_audio_path TEXT,
  source_id TEXT REFERENCES sources(id),
  provenance TEXT NOT NULL DEFAULT 'curated',
  confidence REAL,
  status TEXT NOT NULL DEFAULT 'metadata_ready',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (ipa IS NOT NULL OR audio_source_uri IS NOT NULL OR local_audio_path IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS pronunciations_by_object
  ON pronunciations(object_id, status, confidence DESC);
CREATE VIEW IF NOT EXISTS pronunciation_entries AS
  SELECT id, object_id, ipa, syllables_json, stress_json, variant_code,
         audio_source_uri, local_audio_path, source_id, provenance,
         confidence, status
  FROM pronunciations;
"""


def pronunciation_id(object_id: str) -> str:
    return f"fr:pronunciation:{object_id.removeprefix('fr:')}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.executescript(SCHEMA)

    # Preserve the old `language_objects.ipa` lookup contract while moving its
    # contents into structured records. Future writes must target this table.
    legacy_rows = db.execute(
        "SELECT id, ipa, source_id, provenance FROM language_objects "
        "WHERE ipa IS NOT NULL AND trim(ipa) <> ''"
    ).fetchall()
    for object_id, ipa, source_id, provenance in legacy_rows:
        db.execute(
            "INSERT OR IGNORE INTO pronunciations "
            "(id, object_id, ipa, source_id, provenance, confidence, status) "
            "VALUES (?, ?, ?, ?, ?, 1.0, 'curated')",
            (pronunciation_id(object_id), object_id, ipa, source_id, provenance),
        )

    db.execute(
        "INSERT INTO metadata(key, value) VALUES ('schema_version', '4') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
    )
    db.execute(
        "INSERT INTO metadata(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ('pronunciation_model', 'pronunciations: IPA, syllables, stress, audio references, provenance, confidence'),
    )
    db.commit()
    print(f"Pronunciation schema ready; migrated {len(legacy_rows)} legacy IPA entries.")


if __name__ == '__main__':
    main()
