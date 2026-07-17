#!/usr/bin/env python3
"""Add immutable Learning Resource revisions and parser-safe analysis boundaries.

This is deliberately an additive migration. It does not implement a parser or
an AI provider; it gives either future engine a non-canonical place to record
matches and attach revisable learning material.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import uuid
from pathlib import Path

from canonical_identity import NAMESPACE


MIGRATION_ID = "20260717_learning_revisions_and_analysis_boundaries"

SCHEMA = """
CREATE INDEX IF NOT EXISTS idx_canonical_facts_subject_predicate
  ON canonical_facts(canonical_subject_id, predicate_code);
CREATE INDEX IF NOT EXISTS idx_fact_evidence_source_record
  ON fact_evidence(source_record_id);
CREATE INDEX IF NOT EXISTS idx_fact_code_values_value
  ON fact_code_values(value_code);
CREATE INDEX IF NOT EXISTS idx_fact_number_values_value
  ON fact_number_values(value_number);

CREATE TRIGGER IF NOT EXISTS validate_fact_code_value_kind
BEFORE INSERT ON fact_code_values
WHEN (SELECT value_kind FROM fact_predicates WHERE code =
      (SELECT predicate_code FROM canonical_facts WHERE id = NEW.fact_id)) != 'code'
BEGIN
  SELECT RAISE(ABORT, 'Fact predicate requires a different value type');
END;
CREATE TRIGGER IF NOT EXISTS validate_fact_number_value_kind
BEFORE INSERT ON fact_number_values
WHEN (SELECT value_kind FROM fact_predicates WHERE code =
      (SELECT predicate_code FROM canonical_facts WHERE id = NEW.fact_id)) != 'number'
BEGIN
  SELECT RAISE(ABORT, 'Fact predicate requires a different value type');
END;
CREATE TRIGGER IF NOT EXISTS validate_fact_text_value_kind
BEFORE INSERT ON fact_text_values
WHEN (SELECT value_kind FROM fact_predicates WHERE code =
      (SELECT predicate_code FROM canonical_facts WHERE id = NEW.fact_id)) != 'text'
BEGIN
  SELECT RAISE(ABORT, 'Fact predicate requires a different value type');
END;
CREATE TRIGGER IF NOT EXISTS validate_fact_object_value_kind
BEFORE INSERT ON fact_object_values
WHEN (SELECT value_kind FROM fact_predicates WHERE code =
      (SELECT predicate_code FROM canonical_facts WHERE id = NEW.fact_id)) != 'object'
BEGIN
  SELECT RAISE(ABORT, 'Fact predicate requires a different value type');
END;

CREATE TABLE IF NOT EXISTS learning_resource_revisions (
  id TEXT PRIMARY KEY,
  resource_object_id TEXT NOT NULL REFERENCES learning_resources(resource_object_id) ON DELETE RESTRICT,
  revision_number INTEGER NOT NULL CHECK(revision_number > 0),
  replaces_revision_id TEXT REFERENCES learning_resource_revisions(id) ON DELETE RESTRICT,
  authoring_mode TEXT NOT NULL CHECK(authoring_mode IN ('human','teacher','ai','imported')),
  lifecycle TEXT NOT NULL CHECK(lifecycle IN ('draft','reviewed','published','superseded','deprecated')),
  source_release_id TEXT REFERENCES source_releases(id),
  content_hash TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  published_at TEXT,
  UNIQUE(resource_object_id, revision_number)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_published_learning_resource_revision
  ON learning_resource_revisions(resource_object_id)
  WHERE lifecycle = 'published';
CREATE TABLE IF NOT EXISTS learning_resource_revision_texts (
  id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL REFERENCES learning_resource_revisions(id) ON DELETE RESTRICT,
  language_code TEXT NOT NULL,
  content_role TEXT NOT NULL,
  content_text TEXT NOT NULL,
  UNIQUE(revision_id, language_code, content_role)
);
CREATE TRIGGER IF NOT EXISTS validate_learning_revision_parent
BEFORE INSERT ON learning_resource_revisions
WHEN NEW.replaces_revision_id IS NOT NULL AND NOT EXISTS (
  SELECT 1 FROM learning_resource_revisions parent
  WHERE parent.id = NEW.replaces_revision_id
    AND parent.resource_object_id = NEW.resource_object_id
)
BEGIN
  SELECT RAISE(ABORT, 'A learning-resource revision may replace only its own resource revision');
END;
CREATE TRIGGER IF NOT EXISTS prevent_learning_revision_text_update
BEFORE UPDATE ON learning_resource_revision_texts
BEGIN
  SELECT RAISE(ABORT, 'Learning-resource revision text is immutable; create a new revision');
END;
CREATE TRIGGER IF NOT EXISTS prevent_learning_revision_text_delete
BEFORE DELETE ON learning_resource_revision_texts
BEGIN
  SELECT RAISE(ABORT, 'Learning-resource revision text is immutable; deprecate the revision instead');
END;

CREATE TABLE IF NOT EXISTS sentence_analysis_object_matches (
  id TEXT PRIMARY KEY,
  analysis_id TEXT NOT NULL REFERENCES sentence_analysis_instances(id) ON DELETE CASCADE,
  node_id TEXT REFERENCES sentence_analysis_nodes(id) ON DELETE SET NULL,
  canonical_object_id TEXT REFERENCES canonical_objects(canonical_id) ON DELETE RESTRICT,
  surface_text TEXT NOT NULL,
  start_offset INTEGER,
  end_offset INTEGER,
  match_role TEXT NOT NULL CHECK(match_role IN (
    'lemma','inflected_form','contraction_component','expression','collocation',
    'grammar_construction','sentence_target','unknown'
  )),
  resolution_status TEXT NOT NULL CHECK(resolution_status IN ('resolved','ambiguous','unresolved')),
  engine_kind TEXT NOT NULL CHECK(engine_kind IN ('deterministic','ai_assisted','hybrid')),
  confidence REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_analysis_matches_analysis_span
  ON sentence_analysis_object_matches(analysis_id, start_offset, end_offset);
CREATE INDEX IF NOT EXISTS idx_analysis_matches_canonical_object
  ON sentence_analysis_object_matches(canonical_object_id);
CREATE TABLE IF NOT EXISTS sentence_analysis_learning_resource_links (
  analysis_id TEXT NOT NULL REFERENCES sentence_analysis_instances(id) ON DELETE CASCADE,
  revision_id TEXT NOT NULL REFERENCES learning_resource_revisions(id) ON DELETE RESTRICT,
  role_code TEXT NOT NULL,
  PRIMARY KEY(analysis_id, revision_id, role_code)
);
"""

PREDICATES = [
    ("ipa", "text", "IPA transcription", "International Phonetic Alphabet transcription."),
    ("syllable_segmentation", "text", "Syllable segmentation", "Phonological syllable segmentation."),
    ("stress_pattern", "text", "Stress pattern", "Optional stress or prominence information."),
    ("inflected_form_of", "object", "Inflected form of", "Canonical lemma or base object for an inflected form."),
    ("has_pronunciation", "object", "Has pronunciation", "Pronunciation object associated with this language object."),
    ("grammatical_number", "code", "Grammatical number", "Inherent or realized grammatical number."),
    ("mood", "code", "Mood", "Grammatical mood for a realization."),
    ("tense", "code", "Tense", "Grammatical tense for a realization."),
]


def stable_uuid(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    checksum = hashlib.sha256(SCHEMA.encode()).hexdigest()
    db.execute(
        "INSERT OR IGNORE INTO schema_migrations(id,checksum,description) VALUES (?,?,?)",
        (MIGRATION_ID, checksum, "Immutable Learning Resource revisions and non-canonical parser analysis boundaries."),
    )
    db.executemany(
        "INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES (?,?,?,?)",
        PREDICATES,
    )

    # Existing resource shells get an initial revision without inventing or
    # copying legacy teaching text. A future content migration can add the
    # corresponding immutable revision text while preserving this provenance.
    for resource in db.execute("SELECT resource_object_id,authoring_mode,lifecycle,source_release_id FROM learning_resources"):
        revision_id = stable_uuid("learning-resource-revision", f"{resource['resource_object_id']}|1")
        db.execute(
            """INSERT OR IGNORE INTO learning_resource_revisions
               (id,resource_object_id,revision_number,authoring_mode,lifecycle,source_release_id)
               VALUES (?,?,1,?,?,?)""",
            (revision_id, resource["resource_object_id"], resource["authoring_mode"], resource["lifecycle"], resource["source_release_id"]),
        )

    db.execute(
        """INSERT INTO metadata(key,value) VALUES (?,?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        ("learning_revision_and_analysis_boundary", "Facts are predicate/value/evidence claims; analysis is non-canonical and may link Learning Resource revisions only."),
    )
    db.commit()
    print("Learning revisions and parser analysis boundaries are ready.")


if __name__ == "__main__":
    main()
