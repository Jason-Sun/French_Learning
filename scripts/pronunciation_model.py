#!/usr/bin/env python3
"""Shared source-independent helpers for Liens Pronunciation Objects.

One language object owns one stable Pronunciation Object.  Sources contribute
representations to that object; they never determine its identity.
"""

from __future__ import annotations

import re
import sqlite3
import uuid

from canonical_identity import NAMESPACE, canonical_uuid


def stable_id(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def safe(value: str) -> str:
    return re.sub(r"[^a-z0-9:_-]+", "_", value.casefold()).strip("_")


def pronunciation_object_id(owner_id: str) -> str:
    """Return the stable source-independent Pronunciation Object ID."""
    return f"fr:pronunciation:{safe(owner_id.removeprefix('fr:'))}"


def pronunciation_identity_key(owner_id: str) -> str:
    return f"fr|pronunciation||owner={owner_id}"


def pronunciation_relationship_id(owner_id: str, pronunciation_id: str) -> str:
    return stable_id("relationship", f"{owner_id}|has_pronunciation|{pronunciation_id}")


def add_column_if_missing(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_representation_schema(db: sqlite3.Connection) -> None:
    """Keep representation lifecycle and browser projection metadata additive."""
    db.executescript(
        """
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
        CREATE TABLE IF NOT EXISTS pronunciation_representations (
          id TEXT PRIMARY KEY,
          pronunciation_object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
          representation_kind TEXT NOT NULL,
          transcription_system TEXT,
          value_text TEXT,
          value_json TEXT,
          lifecycle TEXT NOT NULL DEFAULT 'canonical',
          confidence REAL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pronunciation_representation_evidence (
          representation_id TEXT NOT NULL REFERENCES pronunciation_representations(id) ON DELETE CASCADE,
          source_record_id TEXT NOT NULL REFERENCES source_records(id),
          confidence REAL NOT NULL DEFAULT 1.0,
          PRIMARY KEY(representation_id, source_record_id)
        );
        """
    )
    # Variant metadata is part of representation identity.  The old index could
    # collapse two identical IPA strings that have different regional labels.
    db.execute("DROP INDEX IF EXISTS pronunciation_representation_identity")
    db.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS pronunciation_representation_identity
           ON pronunciation_representations(
             pronunciation_object_id, representation_kind,
             COALESCE(transcription_system, ''), COALESCE(value_text, ''),
             COALESCE(value_json, '')
           )"""
    )
    add_column_if_missing(db, "pronunciation_object_details", "representation_lifecycle", "TEXT")
    add_column_if_missing(db, "pronunciation_object_details", "transcription_system", "TEXT")
    add_column_if_missing(db, "pronunciation_object_details", "representation_metadata_json", "TEXT")


def ensure_pronunciation_object(
    db: sqlite3.Connection,
    owner_id: str,
    *,
    display_form: str | None = None,
) -> tuple[str, str]:
    """Return ``(pronunciation_object_id, has_pronunciation_relationship_id)``."""
    # Callers establish the additive representation schema once per import or
    # migration. Rebuilding its identity index here would make a large import
    # rebuild that index once for every language object.
    pronunciation_id = pronunciation_object_id(owner_id)
    if display_form is None:
        row = db.execute(
            "SELECT display_form FROM language_objects WHERE id = ?", (owner_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Pronunciation owner does not exist: {owner_id}")
        display_form = row[0]
    identity_key = pronunciation_identity_key(owner_id)
    db.execute(
        """INSERT OR IGNORE INTO language_objects
           (id, type_code, canonical_form, display_form, normalized_form,
            content_status, provenance)
           VALUES (?, 'pronunciation', ?, ?, ?, 'metadata_ready', 'curated')""",
        (
            pronunciation_id,
            f"{display_form} pronunciation",
            f"{display_form} · pronunciation",
            f"{display_form.casefold()} pronunciation",
        ),
    )
    db.execute(
        """INSERT OR IGNORE INTO canonical_objects
           (canonical_id, language_object_id, object_type_code, identity_key)
           VALUES (?, ?, 'pronunciation', ?)""",
        (canonical_uuid(identity_key), pronunciation_id, identity_key),
    )
    relationship_id = pronunciation_relationship_id(owner_id, pronunciation_id)
    db.execute(
        """INSERT OR IGNORE INTO relationships
           (id, source_object_id, target_object_id, relationship_type_code,
            source_kind, confidence)
           VALUES (?, ?, ?, 'has_pronunciation', 'curated', 1)""",
        (relationship_id, owner_id, pronunciation_id),
    )
    return pronunciation_id, relationship_id
