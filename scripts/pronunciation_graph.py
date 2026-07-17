#!/usr/bin/env python3
"""Graph-native pronunciation storage shared by Liens importers and exporters."""

from __future__ import annotations

import re
import sqlite3
from typing import Iterable


DETAILS_SCHEMA = """
CREATE TABLE IF NOT EXISTS pronunciation_object_details (
  object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE,
  ipa TEXT,
  syllables_json TEXT NOT NULL DEFAULT '[]',
  stress_json TEXT NOT NULL DEFAULT '[]',
  liaison_json TEXT NOT NULL DEFAULT '[]',
  silent_letters_json TEXT NOT NULL DEFAULT '[]',
  elision_json TEXT NOT NULL DEFAULT '[]',
  notes_en TEXT,
  notes_zh TEXT,
  variant_code TEXT NOT NULL DEFAULT 'standard',
  audio_source_uri TEXT,
  local_audio_path TEXT,
  source_id TEXT REFERENCES sources(id),
  provenance TEXT NOT NULL DEFAULT 'curated',
  confidence REAL,
  review_status TEXT NOT NULL DEFAULT 'metadata_ready',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (ipa IS NOT NULL OR audio_source_uri IS NOT NULL OR local_audio_path IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS pronunciation_details_by_variant
  ON pronunciation_object_details(variant_code, review_status, confidence DESC);
"""


def _safe(value: str) -> str:
    return re.sub(r"[^a-z0-9:_-]+", "_", value.casefold()).strip("_")


def graph_object_id(legacy_id: str) -> str:
    """Stable graph-object identity: one node for each legacy pronunciation record."""
    return f"fr:pronunciation_object:{_safe(legacy_id.removeprefix('fr:'))}"


def relationship_id(owner_id: str, pronunciation_id: str) -> str:
    return f"fr:rel:{_safe(owner_id.removeprefix('fr:'))}:has_pronunciation:{_safe(pronunciation_id.removeprefix('fr:'))}"


def ensure_schema(db: sqlite3.Connection) -> None:
    """Additive migration: retain the legacy table while establishing graph nodes."""
    columns = {row[1] for row in db.execute("PRAGMA table_info(pronunciations)")}
    if "pronunciation_object_id" not in columns:
        db.execute(
            "ALTER TABLE pronunciations ADD COLUMN pronunciation_object_id "
            "TEXT REFERENCES language_objects(id)"
        )
    db.executescript(DETAILS_SCHEMA)


def sync_graph(db: sqlite3.Connection) -> int:
    """Materialize every legacy pronunciation record as a first-class graph object.

    The old ``pronunciations`` table stays a supported write/import compatibility
    boundary. This synchronizer is idempotent and makes its records visible as
    ``pronunciation`` Language Objects linked by ``has_pronunciation``.
    """
    ensure_schema(db)
    rows = list(
        db.execute(
            "SELECT p.*, o.display_form FROM pronunciations AS p "
            "JOIN language_objects AS o ON o.id=p.object_id "
            "WHERE p.status <> 'deprecated'"
        )
    )
    for row in rows:
        legacy_id = row[0]
        owner_id = row[1]
        object_id = graph_object_id(legacy_id)
        variant = row[5] or "standard"
        source_id = row[8]
        provenance = row[9]
        confidence = row[10]
        review_status = row[11]
        display_form = row[-1]
        db.execute(
            "INSERT INTO language_objects "
            "(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) "
            "VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET canonical_form=excluded.canonical_form, "
            "display_form=excluded.display_form, source_id=excluded.source_id, "
            "content_status=excluded.content_status, provenance=excluded.provenance",
            (
                object_id,
                "pronunciation",
                f"{display_form} pronunciation ({variant})",
                f"{display_form} · pronunciation",
                f"{display_form.casefold()} pronunciation {variant}",
                source_id,
                review_status,
                provenance,
            ),
        )
        db.execute(
            "INSERT INTO pronunciation_object_details "
            "(object_id,ipa,syllables_json,stress_json,variant_code,audio_source_uri,local_audio_path,source_id,provenance,confidence,review_status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(object_id) DO UPDATE SET ipa=excluded.ipa, "
            "syllables_json=excluded.syllables_json, stress_json=excluded.stress_json, "
            "variant_code=excluded.variant_code, audio_source_uri=excluded.audio_source_uri, "
            "local_audio_path=excluded.local_audio_path, source_id=excluded.source_id, "
            "provenance=excluded.provenance, confidence=excluded.confidence, "
            "review_status=excluded.review_status",
            (
                object_id,
                row[2], row[3], row[4], variant, row[6], row[7], source_id,
                provenance, confidence, review_status,
            ),
        )
        db.execute(
            "UPDATE pronunciations SET pronunciation_object_id=? WHERE id=?",
            (object_id, legacy_id),
        )
        db.execute(
            "INSERT OR IGNORE INTO relationships "
            "(id,source_object_id,target_object_id,relationship_type_code,position,source_kind,confidence) "
            "VALUES (?,?,?,?,NULL,?,?)",
            (relationship_id(owner_id, object_id), owner_id, object_id,
             "has_pronunciation", provenance, confidence if confidence is not None else 1.0),
        )
    return len(rows)
